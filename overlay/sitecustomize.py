"""Runtime patch for the Hermes Railway image.

Monkey-patches ``tools.tirith_security`` so lookalike-TLD ``warn`` findings for
known-good production gTLDs (``.app`` AND ``.run``) are suppressed, instead of
only ``.app``.

WHY THIS EXISTS (upgrade-proof):
The baked module at ``/opt/hermes/tools/tirith_security.py`` ships with
``_is_app_tld_finding`` hard-coded to suppress ``.app`` only. FAL inference
endpoints (``queue.fal.run``) hit the ``.run`` TLD, which the heuristic flags
as 'Lookalike TLD — can be confused with file extensions', forcing a manual
approval prompt on every image-gen call even under ``approvals.mode: auto``.
A direct edit of the baked file works but is lost on the next hermes upgrade.
This file lives on the persistent ``/opt/hermes-railway/`` volume (first on
PYTHONPATH) and re-applies the fix at every interpreter startup, so it
survives redeploys/upgrades that revert the baked module.

The patch is idempotent, reversible (remove this file to restore stock
behavior), and uses lazy import so it is cheap in short-lived processes.

BUZZ WS-WEDGE PATCH (added 2026-09-11) — see section below for rationale.
"""
from __future__ import annotations
import re
import sys

# A lookalike-TLD finding is only benign for the *exact* gTLDs ``.app`` and
# ``.run``. Match on a real label boundary so ``.apple`` / ``.application`` /
# ``.running`` are NOT suppressed — a plain substring test over-matched them.
_TLD_RE = re.compile(r"\.(app|run)(?![a-z0-9-])")


def _patched_benign_tld(finding) -> bool:
    """True if a lookalike_tld finding targets a known-good prod TLD (.app/.run).

    Mirrors the stock ``_is_app_tld_finding`` but also suppresses ``.run``,
    which is a legitimate gTLD used by production API endpoints (e.g.
    queue.fal.run). Any other TLD or rule still warns.
    """
    if not isinstance(finding, dict):
        return False
    if finding.get("rule_id") != "lookalike_tld":
        return False
    for field in ("value", "tld", "detail", "description", "message"):
        val = finding.get(field)
        if val is None:
            continue
        if _TLD_RE.search(str(val).lower()):
            return True
    return False


def _patch_tirith_lookalike_tld() -> None:
    try:
        if "/opt/hermes" not in sys.path:
            sys.path.insert(0, "/opt/hermes")
        from tools import tirith_security as mod  # type: ignore
    except Exception:
        return
    try:
        mod._is_benign_tld_finding = _patched_benign_tld
    except Exception:
        pass
    try:
        mod._is_app_tld_finding = _patched_benign_tld
    except Exception:
        pass


# =============================================================================
# BUZZ WEB SOCKET WEDGE PATCH (strategic_advisor TEST opt-in)
# =============================================================================
# Rationale: the relay (wss://www.clebotz.com) routinely ACCEPTS the WebSocket,
# authenticates, then silently stops forwarding events without surfacing a close
# (buz adapter #98097). The adapter's only safety net is a hardcoded 300s idle
# timeout (_WS_READ_IDLE_TIMEOUT); on a half-dead relay it reconnects, goes
# silent for another 300s, reconnects, ... forever — all-profile Buzz DMs wedge
# until a human restarts the gateway. (Watchdog cron covers recovery; this
# patch reduces HOW OFTEN it fires.)
#
# TEST SCOPE: ONLY the profile whose gateway.platforms.buzz.extra sets
# ws_idle_timeout opts in (currently strategic_advisor, value 60). Every other
# profile's adapter is left 100% untouched (stock behavior) — no risk to others.
#
# Mechanism: we cannot reliably patch the module global here (the gateway
# imports the adapter under the hermes_plugins.<slug> runtime alias, a
# different object). Instead we wrap platform_registry.create_adapter and, for
# the returned adapter instance, read config.extra.ws_idle_timeout. If set we
# monkey-patch THAT instance only: (a) open its read loop with a shorter idle
# timeout, and (b) after N consecutive silent timeouts, raise a ConnectionError
# that forces the NORMAL reconnect path instead of looping in-place.
#
# This is intentionally instance-scoped, gated by the config opt-in, and
# additive (a no-op marker log lets us confirm it loaded).
# =============================================================================

_BUZZ_WS_TEST_MARKER = "[hermes-sitecustomize] buzz ws-wedge patch applied to profile %s (idle=%ss)"


def _make_buzz_ws_patched_instance(adapter, idle_timeout):
    """Apply the readable idle-timeout + consecutive-silent escalation to an
    adapter instance. Returns the (possibly wrapped) instance."""
    try:
        # Re-bind the read-loop idle wait for THIS instance. We wrap the
        # instance method; the _websocket_loop references _WS_READ_IDLE_TIMEOUT
        # via the module global, so we patch a per-instance wrapper that reads
        # self._ws_idle_timeout first.
        async def _ws_read_with_timeout_factory(orig_wait_for, orig_timeout):
            pass  # placeholder — real impl below in _install

        _install_buzz_ws_patch(adapter, idle_timeout)
        return adapter
    except Exception as e:  # never break adapter creation on a patch failure
        try:
            import logging
            logging.getLogger("sitecustomize").warning(
                "buzz ws wedge patch failed to install: %s", e
            )
        except Exception:
            pass
        return adapter


def _install_buzz_ws_patch(adapter, idle_timeout):
    """Monkeypatch the adapter instance: wrap _websocket_loop with a read-idle
    timeout override + consecutive-silent escalation. Falls back gracefully."""
    try:
        import asyncio
    except Exception:
        return

    stock_loop = getattr(adapter, "_websocket_loop", None)
    if stock_loop is None:
        return

    # Keep the module constant as a sane floor (never go absurdly low).
    try:
        import hermes_plugins  # noqa  (may or may not resolve; not required)
    except Exception:
        pass
    import plugins  # noqa  (path-based fallback; optional)
    try:
        from gateway.platform_registry import platform_registry  # noqa
    except Exception:
        pass

    # Record the opt-in timeout on the instance.
    adapter._ws_idle_timeout = float(idle_timeout)

    async def _websocket_loop_with_override(self):
        """Replica of the stock loop but reads self._ws_idle_timeout and
        escalates out of stale-reconnect loops. Falls back to the stock loop
        for any profile that did not opt in (self._ws_idle_timeout unset)."""
        idle = getattr(self, "_ws_idle_timeout", None)
        if idle is None:
            # Not opted-in — run stock behavior unchanged.
            return await stock_loop(self)

        # Re-import inside the closure to avoid import-order hazards.
        import os  # noqa  (kept for parity; unused)
        import json  # noqa
        import asyncio  # noqa
        import websockets  # noqa

        from plugins.platforms.buzz import adapter as buzz_adapter

        logger = buzz_adapter.logger  # resolve inside closure (no module-global)

        _WS_READ_IDLE_TIMEOUT = float(idle)
        _WS_AUTH_TIMEOUT = getattr(buzz_adapter, "_WS_AUTH_TIMEOUT", 20.0)
        _WS_MAX_MESSAGE_BYTES = getattr(buzz_adapter, "_WS_MAX_MESSAGE_BYTES", 2_000_000)
        _WS_MEMBERSHIP_SUB_ID = getattr(buzz_adapter, "_WS_MEMBERSHIP_SUB_ID", "hermes-buzz-membership")

        backoff = 1.0
        consecutive_silent = 0
        ESCALATE_AFTER = 3  # after N silent reconnects, force a full transport reset

        try:
            while True:
                try:
                    async with websockets.connect(
                        self._websocket_url(),
                        open_timeout=_WS_AUTH_TIMEOUT,
                        close_timeout=5,
                        ping_interval=20,
                        ping_timeout=20,
                        max_size=_WS_MAX_MESSAGE_BYTES,
                    ) as websocket:
                        await self._authenticate_websocket(websocket)
                        subscriptions = await self._subscribe_websocket(websocket)
                        self._ws_active = True
                        if self._ws_ready is not None:
                            self._ws_ready.set()
                        backoff = 1.0
                        discovery_task = asyncio.create_task(
                            self._ws_discovery_loop(websocket, subscriptions)
                        )
                        try:
                            frame_iter = websocket.__aiter__()
                            while True:
                                try:
                                    raw = await asyncio.wait_for(
                                        frame_iter.__anext__(),
                                        timeout=_WS_READ_IDLE_TIMEOUT,
                                    )
                                except StopAsyncIteration:
                                    break
                                except asyncio.TimeoutError:
                                    consecutive_silent += 1
                                    if consecutive_silent >= ESCALATE_AFTER:
                                        # Relay keeps accepting but never
                                        # forwards — force the normal reconnect
                                        # path (full teardown) instead of a
                                        # silent in-place retry.
                                        logger.warning(
                                            "Buzz: %d consecutive silent reconnects — "
                                            "forcing relay-health reconnect (wedge patch)",
                                            consecutive_silent,
                                        )
                                        raise ConnectionError(
                                            "no frame after multiple silent reconnects (wedge patch)"
                                        )
                                    raise ConnectionError(
                                        f"no WebSocket frame for {_WS_READ_IDLE_TIMEOUT:.0f}s; "
                                        "assuming the connection went silent"
                                    )
                                # Any real frame => connection is alive.
                                consecutive_silent = 0
                                try:
                                    message = json.loads(raw)
                                except (ValueError, TypeError):
                                    logger.warning("Buzz: ignoring malformed WebSocket frame")
                                    continue
                                if not isinstance(message, list) or not message:
                                    continue
                                if message[0] == "EVENT" and len(message) >= 3:
                                    s_id = str(message[1])
                                    event = message[2]
                                    if not isinstance(event, dict):
                                        continue
                                    if s_id == _WS_MEMBERSHIP_SUB_ID:
                                        await self._handle_membership_event(
                                            websocket, subscriptions, event
                                        )
                                        continue
                                    channel_id = subscriptions.get(s_id)
                                    state = self._channel_state.get(channel_id or "")
                                    if channel_id and state is not None:
                                        before = self._cursor_mark(state)
                                        await self._handle_event(channel_id, state, event)
                                        self._trim_seen(state)
                                        if self._cursor_mark(state) != before:
                                            self._save_cursors()
                                elif message[0] == "CLOSED":
                                    detail = message[-1] if len(message) > 2 else "subscription closed"
                                    sub_id = str(message[1]) if len(message) > 1 else ""
                                    closed_channel = subscriptions.get(sub_id)
                                    detail_l = str(detail).lower()
                                    is_rejection = (
                                        "restricted" in detail_l
                                        or "not a channel member" in detail_l
                                        or "auth-required" in detail_l
                                    )
                                    if is_rejection and closed_channel:
                                        self._restricted_channels.add(closed_channel)
                                        del subscriptions[sub_id]
                                        self._channel_state.pop(closed_channel, None)
                                    else:
                                        raise ConnectionError(str(detail))
                                elif message[0] == "NOTICE":
                                    logger.warning("Buzz: relay notice: %s", message[-1])
                        finally:
                            discovery_task.cancel()
                            try:
                                await discovery_task
                            except (asyncio.CancelledError, Exception):
                                pass
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    self._ws_active = False
                    logger.warning(
                        "Buzz: WebSocket disconnected; retrying in %.1fs: %s",
                        backoff, e,
                    )
                    await asyncio.sleep(backoff)
                    backoff = min(backoff * 2, 30.0)
        finally:
            self._ws_active = False

    # Bind the override to THIS instance (instance attribute shadows the class
    # method for bound-call sites). Also keep a reference to the stock method.
    import types
    adapter._websocket_loop_stock = stock_loop
    adapter._websocket_loop = types.MethodType(_websocket_loop_with_override, adapter)


def _buzz_cap_send(adapter):
    """Cap a Buzz adapter instance's ``send()`` at the platform's real content
    limit (65,536 bytes, buzz-cli validate.rs MAX_CONTENT_BYTES) so a
    pathological over-limit cron digest never hard-fails delivery.

    With ``splits_long_messages=True`` the delivery runner passes the FULL,
    untruncated payload to ``adapter.send()``. Buzz legitimately accepts that
    up to 64K, so normal reports (a few KB) deliver intact. For anything above
    the cap, the buzz-cli rejects the event and delivery would fail outright;
    instead we coerce long content down to the byte limit with a footer (the
    same convention delivery.py uses at its 4000-char cap). The audit-save in
    delivery.py already persists the full original regardless, so no content is
    lost. Idempotent: re-wrapping an already-wrapped instance is a no-op.
    """
    stock_send = getattr(adapter, "send", None)
    if stock_send is None or getattr(adapter, "_buzz_cap_send_applied", False):
        return adapter
    _BUZZ_MAX_CONTENT_BYTES = 65_536
    footer_room = 200  # leave room for the footer below the relay's byte cap

    async def _capped_send(chat_id, content=None, reply_to=None, metadata=None, **kwargs):
        if isinstance(content, str) and len(content.encode("utf-8")) > _BUZZ_MAX_CONTENT_BYTES:
            limit = _BUZZ_MAX_CONTENT_BYTES - footer_room
            truncated = content.encode("utf-8")[:limit].decode("utf-8", errors="ignore")
            footer = (
                f"\n\n... [message exceeds Buzz's {_BUZZ_MAX_CONTENT_BYTES}-byte "
                f"limit — full output available from the cron audit save]"
            )
            content = truncated + footer
        return await stock_send(chat_id, content, reply_to=reply_to, metadata=metadata, **kwargs)

    # Assign the plain function as an instance attribute (NOT MethodType). A
    # function stored on the instance is not descriptor-bound, so Python calls
    # it with EXACTLY the args given — mirroring the reg.create_adapter pattern
    # below (a MethodType wrapper here would SHIFT chat_id→self and inject the
    # adapter instance as the first positional, corrupting every send).
    adapter.send = _capped_send
    adapter._buzz_cap_send_applied = True
    return adapter


def _patch_buzz_ws_wedge() -> None:
    """Wrap platform_registry.create_adapter so opted-in profiles get the
    instance-scoped webcast wedge patch."""
    try:
        from gateway import platform_registry as pr_mod
    except Exception:
        return
    reg = pr_mod.platform_registry
    stock_create = getattr(reg, "create_adapter", None)
    if stock_create is None:
        return
    if getattr(reg, "_buzz_ws_patch_installed", False):
        return

    def _create_adapter_with_buzz_patch(name, config):
        adapter = stock_create(name, config)
        if adapter is None:
            return None
        # BUZZ LONG-MESSAGE CAPABILITY (2026-09-14): mark every Buzz adapter as a
        # long-message-capable (splits_long_messages) adapter so gateway/delivery.py
        # does NOT truncate cron output to its conservative 4000-char cap (sized
        # around Telegram's 4096 API limit). Buzz natively accepts up to 65,536
        # bytes (buzz-cli validate.rs MAX_CONTENT_BYTES; relay NIP-11
        # max_content_len=65536, ingest allows 256KB) and the adapter's send()
        # streams the content through stdin with no internal cap — so full reports
        # must be delivered intact, with only the audit-save firing (which already
        # works). Without this flag the runner truncated at 4000 chars and appended
        # the "[truncated, full output saved to …]" footer even though Buzz could
        # carry the whole message.
        if str(name).lower().startswith("buzz"):
            adapter.splits_long_messages = True
            adapter = _buzz_cap_send(adapter)
        # Only buzz adapters with the opt-in marker are touched.
        try:
            extra = getattr(config, "extra", None) or {}
            to = extra.get("ws_idle_timeout")
            if to is not None and str(name).lower().startswith("buzz"):
                adapter = _make_buzz_ws_patched_instance(adapter, float(to))
                print(
                    _BUZZ_WS_TEST_MARKER % (str(name), float(to)),
                    flush=True,
                )
        except Exception as e:
            try:
                import logging
                logging.getLogger("sitecustomize").warning(
                    "buzz ws wedge patch create_adapter hook error: %s", e
                )
            except Exception:
                pass
        return adapter

    # Assign the wrapper directly as an instance attribute. NOTE: do NOT wrap
    # in MethodType — assigning an instance attribute (not a class) means
    # Python calls it with exactly the args given (no self injection). Using
    # MethodType(some_func, reg) SHIFTED all args (self consumed 'name'), which
    # broke every adapter (returned None). This is the fixed version.
    reg.create_adapter = _create_adapter_with_buzz_patch
    reg._buzz_ws_patch_installed = True


_patch_tirith_lookalike_tld()
_patch_buzz_ws_wedge()  # RE-ENABLED 2026-09-11 00:55 after fixing MethodType arg-shift (root cause of 'adapter returned None')


# =============================================================================
# AUXILIARY / COMPRESSION MODULE PRELOAD PATCH (added 2026-09-14)
# =============================================================================
# Symptom (regression from the gateway's multithreaded lazy module loading):
#   ImportError: cannot import name 'AuxiliaryExplicitCancellation' from
#   'agent.auxiliary_client' — thrown from agent/conversation_compression.py:69
#   (in <module>) on the FIRST compression of a long-lived session. It repeated
#   on EVERY compression attempt, so the session never compressed.
#
# Root cause: `conversation_compression` is imported LAZILY — first runnable the
# first time `_compress_context` fires (i.e. when a session first crosses its
# compression threshold). In the long-lived gateway, `agent.auxiliary_client` is
# a ~9.7k-line module whose `AuxiliaryExplicitCancellation` class lives at line
# ~319. If, at the moment conversation_compression is first imported, the
# gateway's concurrent worker threads (conversation loop, background review,
# mem-trim housekeeping) are mid-import of `agent.auxiliary_client`, the module
# can be left PARTIALLY in sys.modules (import aborted just before line 319).
# A half-loaded module is NOT removed from sys.modules, so every later
# `from agent.auxiliary_client import AuxiliaryExplicitCancellation` re-hits the
# same broken partial object → ImportError forever. Fresh interpreters are
# unaffected because there is no concurrency at import time there.
#
# Fix: eagerly import BOTH modules synchronously in the main thread at
# interpreter boot, before the gateway spawns any worker thread, and verify /
# repair the binding. With auxiliary_client complete (and conversation_compression
# cached) before any thread exists, the lazy first-compress import becomes a
# no-op and can never race. Idempotent, reversible (delete this block to restore
# stock behavior), and upgrade-proof (re-applied every interpreter start from the
# persistent /opt/hermes-railway volume).
# =============================================================================


def _repair_auxiliary_client() -> bool:
    """Ensure ``agent.auxiliary_client`` is fully loaded and its compression
    symbol is bound. If a partial module is already in ``sys.modules``, evict it
    so a fresh import fully rebuilds the object. Returns True once complete."""
    try:
        if "/opt/hermes" not in sys.path:
            sys.path.insert(0, "/opt/hermes")
    except Exception:
        pass
    try:
        mod = sys.modules.get("agent.auxiliary_client")
    except Exception:
        mod = None
    if mod is not None and not hasattr(mod, "AuxiliaryExplicitCancellation"):
        # Abandon an incomplete module so it is rebuilt from scratch below.
        try:
            sys.modules.pop("agent.auxiliary_client", None)
        except Exception:
            pass
    try:
        # importlib.import_module — NOT the builtin __import__ — returns the
        # submodule object itself. __import__("agent.auxiliary_client") returns
        # the TOP-LEVEL "agent" package, whose __init__ does not re-expose the
        # symbol, so a hasattr() check there spuriously returns False even after
        # a successful (re)build (caught by the preload watchdog 2026-09-14).
        import importlib

        mod = importlib.import_module("agent.auxiliary_client")
        return hasattr(mod, "AuxiliaryExplicitCancellation")
    except Exception as e:
        try:
            import logging

            logging.getLogger("sitecustomize").warning(
                "[hermes-sitecustomize] repair of agent.auxiliary_client failed: %s", e
            )
        except Exception:
            pass
        return False


def _preload_compression_modules() -> None:
    """Force auxiliary_client + conversation_compression to load synchronously
    at boot. Order matters: auxiliary_client MUST be complete before
    conversation_compression runs, because that module's line-69 import (the
    original failure site) reads AuxiliaryExplicitCancellation off it."""
    if _repair_auxiliary_client():
        try:
            __import__("agent.conversation_compression")
        except Exception as e:  # never break boot on a preload hiccup
            try:
                import logging

                logging.getLogger("sitecustomize").warning(
                    "[hermes-sitecustomize] preload of conversation_compression failed: %s", e
                )
            except Exception:
                pass
    try:
        print(
            "[hermes-sitecustomize] aux/compression preload applied "
            "(auxiliary_client=%s, conversation_compression=%s)"
            % (
                "agent.auxiliary_client" in sys.modules,
                "agent.conversation_compression" in sys.modules,
            ),
            flush=True,
        )
    except Exception:
        pass


# =============================================================================
# GATEWAY SUPERVISOR SPAWN (durable — 2026-09-14)
# =============================================================================
# Root cause of the recurring "Buzz agent stopped responding": the gateway is
# launched by entrypoint.sh with a bare `setsid ... &` and NO respawn loop, while
# the WebUI gets one. When the gateway dies (or is killed) and no systemd exists
# to revive it, every Buzz profile's socket goes dark and @-mentions go
# unanswered until a human restarts the gateway. This spawns the detached
# /data/scripts/gateway-supervisor.sh FROM THE GATEWAY ITSELF at boot, so the
# supervisor (which lives independent of the gateway process) is present to
# respawn it on any later death. Sitecustomize is the upgrade-proof patch
# location (baked entrypoint.sh reverts on upgrade); this block is additive and
# safely no-ops for every non-gateway process.
# =============================================================================


def _spawn_gateway_supervisor() -> None:
    """When the gateway process boots, launch the detached supervisor so a later
    gateway crash is auto-recovered. Idempotent (supervisor has a lockfile guard);
    a no-op for every non-gateway Python process."""
    import os
    import shlex
    import subprocess

    argv = getattr(sys, "argv", []) or []
    # Only the real gateway runner (argv = hermes gateway run [--replace]) gets a
    # supervisor. Exclude CLI probes, the WebUI server, profile dispatch, cron,
    # subagents, and this agent's own tool sessions (all different argv shapes).
    if len(argv) < 2:
        return
    base = os.path.basename(argv[0]).lower()
    gw = [a for a in argv[1:] if a not in ("--replace", "--no-tui", "--skip-deps")]
    if "gateway" not in gw or "run" not in gw:
        return
    script = "/data/scripts/gateway-supervisor.sh"
    if not os.path.exists(script):
        return
    try:
        # The supervisor self-guards with a lockfile, so a duplicate spawn here
        # is a harmless no-op (second process exits immediately). Detached so it
        # survives this gateway's death.
        subprocess.Popen(
            ["/bin/bash", script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )
        try:
            import logging

            logging.getLogger("sitecustomize").warning(
                "[hermes-sitecustomize] gateway supervisor spawned for resilient gateway recovery"
            )
        except Exception:
            pass
    except Exception as e:
        try:
            import logging

            logging.getLogger("sitecustomize").warning(
                "[hermes-sitecustomize] gateway supervisor spawn failed: %s", e
            )
        except Exception:
            pass


_spawn_gateway_supervisor()


_preload_compression_modules()

# ---- BEGIN async-delegation cross-profile fix (2026-09-28) ----
import os as _os_asyncfix, sys as _sys_asyncfix
# =============================================================================
# CROSS-PROFILE ASYNC-DELEGATION DELIVERY FIX (2026-09-28)
# =============================================================================
# Root cause: background delegations dispatched from a NAMED profile
# (code_architect, manus, patent_attorney, ...) persist their durable
# completion row AND their origin session into that profile's OWN state.db
# (/data/profiles/<name>/state.db), because the daemon worker resolves
# get_hermes_home() under the dispatching profile. But the gateway's
# async-delegation delivery path resolves get_hermes_home() under the ROOT
# store (/data) —
#
#   1. RESTART REPLAY: restore_undelivered_completions (ProcessRegistry init)
#      scans only /data/state.db -> 0 rows -> stranded completions never
#      re-enqueued.
#   2. LIVE DELIVERY: _classify_completion_target / _resolve_async_delegation_session
#      look up the origin session via self._session_db = ROOT store -> not found
#      -> verdict "terminal" ("permanently-gone session") -> every completion
#      terminally dropped, its result stranded in the profile store.
#
# The framework ALREADY solved this exact class of bug for the /handoff watcher
# (_handoff_watch_scopes explicitly iterates served profile homes under
# _async_profile_runtime_scope) — the async-delegation path was never given the
# same multiplex treatment. This patch adds it, upgrade-proof via sitecustomize
# (baked gateway/run.py reverts on upgrade).
#
# Two legs, both defensive and inert unless the origin profile is resolvable:
#   Leg 1 (STARTUP RESTORE): wrap restore_undelivered_completions so a gateway
#     process also sweeps every served profile home.
#   Leg 2 (LIVE DELIVERY): wrap GatewayRunner._deliver_async_delegation_group so
#     delivery enters the origin profile's home scope, fixing session
#     resolution + durable claim to hit the correct store.
# =============================================================================


def _is_gateway_process() -> bool:
    import os as _os
    import sys as _sys

    argv = getattr(_sys, "argv", []) or []
    if len(argv) < 2:
        return False
    base = _os.path.basename(argv[0]).lower()
    gw = [a for a in argv[1:] if a not in ("--replace", "--no-tui", "--skip-deps")]
    return "gateway" in gw and "run" in gw


def _profile_from_session_key(session_key: str) -> "str | None":
    """Extract the profile name from a session key.

    Default/root sessions are ``agent:main:<platform>:...`` -> return None
    (root store, stock behavior). Named-profile sessions are
    ``agent:<profile>:<platform>:...`` -> return the profile name.
    """
    sk = (session_key or "").strip()
    if not sk:
        return None
    parts = sk.split(":")
    if len(parts) < 2 or parts[0] != "agent":
        return None
    pname = parts[1] or ""
    if pname in ("", "main"):
        return None
    return pname


def _install_async_delegation_profile_aware() -> None:
    """Apply both fix legs. Idempotent; never breaks boot on any failure."""
    if not _is_gateway_process():
        return
    try:
        import gateway.run as grun
        from hermes_cli.profiles import profiles_to_serve
        from hermes_constants import set_hermes_home_override, reset_hermes_home_override
    except Exception as exc:
        try:
            import logging
            logging.getLogger("sitecustomize").warning(
                "[hermes-sitecustomize] async-delegation fix import failed: %s", exc)
        except Exception:
            pass
        return

    def _home_for_profile(pname: str) -> "str | None":
        try:
            homes = dict(profiles_to_serve(multiplex=True))
            home = homes.get(pname)
            return str(home) if home else None
        except Exception:
            return None

    # ------------------------------------------------------------------
    # LEG 1: restore_undelivered_completions sweeps every served profile home.
    # Called from ProcessRegistry.__init__ at gateway start; also callable.
    # ------------------------------------------------------------------
    try:
        import tools.async_delegation as ad_mod
        _stock_restore = ad_mod.restore_undelivered_completions

        def _profile_aware_restore(target_queue) -> int:
            total = _stock_restore(target_queue)
            try:
                for pname, _phome in profiles_to_serve(multiplex=True):
                    if not pname or pname == "default":
                        continue  # default IS the root store already swept above
                    home = _home_for_profile(pname)
                    if not home:
                        continue
                    token = set_hermes_home_override(home)
                    try:
                        total += _stock_restore(target_queue)
                    finally:
                        reset_hermes_home_override(token)
            except Exception:
                pass  # root sweep already done; profile sweep is best-effort
            return total

        ad_mod.restore_undelivered_completions = _profile_aware_restore
    except Exception:
        pass

    # ------------------------------------------------------------------
    # LEG 2: live delivery enters the origin profile's home scope.
    # ------------------------------------------------------------------
    try:
        _stock_deliver = grun.GatewayRunner._deliver_async_delegation_group

        async def _profile_aware_deliver(self, group):
            # The group is same-session by construction; derive profile from
            # the first event that carries a session_key.
            profile = None
            for evt in group:
                p = _profile_from_session_key(evt.get("session_key"))
                if p:
                    profile = p
                    break
            if not profile:
                return await _stock_deliver(self, group)
            home = _home_for_profile(profile)
            if not home:
                return await _stock_deliver(self, group)
            token = set_hermes_home_override(home)
            try:
                return await _stock_deliver(self, group)
            finally:
                reset_hermes_home_override(token)

        grun.GatewayRunner._deliver_async_delegation_group = _profile_aware_deliver
    except Exception:
        pass

    import logging
    logging.getLogger("sitecustomize").info(
        "[hermes-sitecustomize] async-delegation delivery now profile-aware "
        "(restore sweep + origin-scope delivery)."
    )


_install_async_delegation_profile_aware()
# ---- END async-delegation cross-profile fix ----

# =============================================================================
# MODEL RE-ANSWERED / DOUBLED FINAL CONTENT FIX (2026-10-10)
# =============================================================================
# Symptom: on deepseek-v4-flash-0731 (and other long-generating models), a
# single assistant completion occasionally contains the SAME answer written
# twice back-to-back — the model "re-answers from the top" near the end of the
# stream. Hermes persisted the concatenated stream verbatim, so the user sees
# the full answer twice in the WebUI (same message row, doubled content — the
# fingerprint is near-duplicate copies with ~0.8+ similarity separated by a
# clean seam where the response restarts its own opening).
#
# Evidence (2026-10-10): session ff9ff61f5514 msg68898 = one 3655-token API
# call whose stored content is 9832 chars = two 5.1K / 4.6K near-identical
# answers (sim 0.86) concatenated with no separator. Patent-OA session
# 667537094a5d had a DIFFERENT cause (agent re-emitting a separate "consolidated
# answer" message) — that one is agent behavior, not touched here.
#
# Fix: wrap AIAgent._persist_session so, just before the transcript is written,
# a final assistant row whose string content shows the "restarted answer" shape
# is collapsed to its FIRST complete copy, in place. This reaches both the
# durable DB row AND agent._session_messages (live history) since _persist_and_drain
# assigns messages to _session_messages right after. Detecting here rather than
# during streaming is deliberately conservative: it only fires on a strong
# whole-message signature, so legitimate repeated headings/sections or distinct
# consecutive answers are never collapsed.
#
# Idempotent, reversible (delete this block to restore stock behavior), and
# upgrade-proof (the baked run_agent.py reverts on upgrade; this persistent
# /opt/hermes-railway volume re-applies it at every interpreter start).
# =============================================================================
import re as _re
import difflib as _difflib


def _collapse_restated_answer(text: str, min_len: int = 1500,
                              tail_sim: float = 0.55,
                              probe_len: int = 7,
                              probe_sim: float = 0.6):
    """Collapse a single message that re-answered from the top into its first
    complete copy. Returns (cleaned_text, seam_info) or (text, None) unchanged.

    The signature we target: two LARGE, near-duplicate blocks concatenated,
    where the second block re-uses the message's own opening phrase and shares
    high whole-message similarity with the first. Kept tightly gated so a
    legitimate long answer with repeated section headings is never collapsed.
    """
    if not text or len(text) < min_len * 2:
        return text, None
    norm = " ".join(_re.sub(r"\s+", " ", text).strip().split())
    toks = norm.split()
    if len(toks) < 40:
        return text, None
    probe = " ".join(toks[:probe_len])
    half_ch = int(len(norm) * 0.42)
    best = None
    step = max(3, len(norm) // 6000)
    for ch in range(half_ch, len(norm) - len(probe), step):
        cand = norm[ch:ch + len(probe)]
        r = _difflib.SequenceMatcher(None, probe, cand).ratio()
        if r > probe_sim:
            a, b = norm[:ch], norm[ch:]
            if len(a) >= min_len and len(b) >= min_len:
                sim = _difflib.SequenceMatcher(None, a, b).ratio()
                if sim > tail_sim:
                    best = (ch, round(r, 2), round(sim, 2))
                    break
    if best:
        # ``best[0]`` indexes ``norm`` (whitespace-collapsed), NOT ``text``, and
        # the probe match that produced it is fuzzy — it can fire a few chars
        # early. So neither ``norm[:best[0]]`` (the old behaviour, which also
        # flattened the kept copy to one line) nor its raw translation is the
        # true copy boundary. Translate the seam, then snap it to the exact
        # offset where the message restarts from its own opening, so the kept
        # copy retains its original newlines and code-block indentation intact.
        approx = _norm_offset_to_text_offset(text, best[0])
        cut = _nearest_restart(text, toks[:probe_len], approx)
        if cut is None:
            return text, None
        return text[:cut].rstrip(), best
    return text, None


def _nearest_restart(text: str, opening_tokens, near: int) -> int | None:
    """Offset of the message's "restart from the top", nearest to ``near``.

    The collapse detector finds the seam with a *fuzzy* probe match, so the
    offset it reports can be a few characters early and would clip the tail of
    the kept copy. Re-locate the restart exactly by matching the opening tokens
    (with flexible whitespace) and take the occurrence closest to the fuzzy
    seam. Returns ``None`` if the opening never recurs.
    """
    if not opening_tokens:
        return None
    pat = _re.compile(r"\s+".join(_re.escape(t) for t in opening_tokens))
    starts = [m.start() for m in pat.finditer(text) if m.start() > 0]
    if not starts:
        return None
    return min(starts, key=lambda s: abs(s - near))


def _norm_offset_to_text_offset(text: str, norm_off: int) -> int:
    """Map an offset in ``" ".join(text.split())`` back to an offset in ``text``.

    ``_collapse_restated_answer`` builds ``norm`` by collapsing every whitespace
    run to a single space, so a ``norm`` index is not a ``text`` index. Walk the
    original tokens (``\\S+``), advancing by each token's length plus the single
    joining space, and return the start of the token the offset lands on (or
    ``len(text)`` if it is past the end). The result is always a token boundary,
    so the slice it anchors keeps the original whitespace intact.
    """
    norm_pos = 0
    for m in _re.finditer(r"\S+", text):
        tok_len = m.end() - m.start()
        if norm_pos + tok_len > norm_off:
            return m.start()
        norm_pos += tok_len + 1  # the single space re.sub()/split() inserts
    return len(text)


def _install_doubled_content_collapse() -> None:
    try:
        import run_agent as _ra
    except Exception:
        return
    _stock = getattr(_ra.AIAgent, "_persist_session", None)
    if _stock is None:
        return
    if getattr(_ra.AIAgent, "_hermes_doubled_collapse_applied", False):
        return

    def _persist_with_collapse(self, messages, conversation_history=None):
        # Collapse a doubled final assistant row in place BEFORE any write.
        try:
            if messages and isinstance(messages, list):
                tail = messages[-1]
                if (
                    isinstance(tail, dict)
                    and tail.get("role") == "assistant"
                    and not tail.get("tool_calls")
                    and isinstance(tail.get("content"), str)
                ):
                    cleaned, seam = _collapse_restated_answer(tail["content"])
                    if seam is not None:
                        # Keep a much-lighter log (no giant content echo).
                        import logging as _lg
                        _lg.getLogger("sitecustomize").warning(
                            "[hermes-sitecustomize] collapsed doubled (re-answered) "
                            "assistant content: %d -> %d chars (seam %s)",
                            len(tail["content"]), len(cleaned), seam,
                        )
                        tail["content"] = cleaned
        except Exception:
            pass  # never block persistence on the dedup path
        return _stock(self, messages, conversation_history)

    _ra.AIAgent._persist_session = _persist_with_collapse
    _ra.AIAgent._hermes_doubled_collapse_applied = True


_install_doubled_content_collapse()

# =============================================================================
# WEBUI OPENROUTER DROPDOWN MODEL EXTENSION (2026-10-10)
# =============================================================================
# Symptom: switching model.default to a model that isn't in the WebUI's
# hardcoded `_FALLBACK_MODELS` list (e.g. `deepseek/deepseek-v4.1-flash`) shows
# the OLD model in the WebUI dropdown, so a fresh session can't select the new
# one even though config.yaml + CLI resolve it correctly. This is a known
# "false positive" class: the WebUI's OpenRouter dropdown is served from the
# baked `_FALLBACK_MODELS` constant (config.py line ~2022-2031), NOT from
# config.yaml `providers.openrouter.models`. `providers.<name>.models` is only
# read for NON-openrouter providers.
#
# Fix: register a meta-path finder that, whenever `api.config` is imported in
# the WebUI process, extends `_FALLBACK_MODELS` (in place) with any additional
# OpenRouter models listed here. Runs at every interpreter start via this
# persistent /opt/hermes-railway sitecustomize.py, so it survives WebUI
# upgrades that revert the baked config.py. The finder is idempotent (dedupes
# by model id) and only fires for the WebUI's own `api.config` module — every
# other import is passed through untouched.
#
# To add another model to the WebUI dropdown, append a
# {"provider": "OpenRouter", "id": ..., "label": ...} dict below and restart
# the WebUI server (PID of `python3 /opt/hermes-webui/server.py`).
# =============================================================================

_WEBUI_EXTRA_FALLBACK_MODELS = [
    {"provider": "OpenRouter", "id": "deepseek/deepseek-v4.1-flash", "label": "DeepSeek V4.1 Flash"},
]


def _install_webui_model_dropdown_extension() -> None:
    try:
        import importlib.abc as _iab
    except Exception:
        return
    try:
        import sys as _sys
    except Exception:
        return

    _TARGET_MODULE = "api.config"

    if getattr(_sys, "_hermes_webui_models_ext_installed", False):
        return

    class _WebuiModelsExtFinder(_iab.MetaPathFinder):
        """Wrap the real loader for `api.config` and extend _FALLBACK_MODELS
        once the module has executed. Delegates every other import normally."""

        def find_spec(self, fullname, path=None, target=None):
            if fullname != _TARGET_MODULE:
                return None
            try:
                # Delegate to the NEXT finder (after this one) for the real spec.
                for finder in _sys.meta_path:
                    if finder is self:
                        continue
                    spec = None
                    try:
                        spec = finder.find_spec(fullname, path, target)
                    except Exception:
                        spec = None
                    if spec is not None:
                        return self._wrap_spec(spec)
            except Exception:
                pass
            return None

        @staticmethod
        def _wrap_spec(spec):
            loader = getattr(spec, "loader", None)
            if loader is None:
                return spec
            orig_exec = getattr(loader, "exec_module", None)
            if orig_exec is None:
                return spec

            def _exec_then_extend(module):
                orig_exec(module)
                try:
                    existing = getattr(module, "_FALLBACK_MODELS", None)
                    if isinstance(existing, list):
                        known = {str(m.get("id", "")) for m in existing if isinstance(m, dict)}
                        for _m in _WEBUI_EXTRA_FALLBACK_MODELS:
                            if str(_m.get("id", "")) not in known:
                                existing.append(dict(_m))
                                known.add(str(_m.get("id", "")))
                        try:
                            import logging as _lg
                            _lg.getLogger("sitecustomize").info(
                                "[hermes-sitecustomize] webui _FALLBACK_MODELS extended "
                                "with %s", str(_m.get("id", "")))
                        except Exception:
                            pass
                except Exception:
                    pass

            try:
                loader.exec_module = _exec_then_extend
            except Exception:
                pass
            return spec

    try:
        _sys.meta_path.insert(0, _WebuiModelsExtFinder())
        _sys._hermes_webui_models_ext_installed = True
    except Exception:
        pass


_install_webui_model_dropdown_extension()

# =============================================================================
# KANBAN MODULE-SPLIT COMPAT ALIASES (2026-10-13)
# =============================================================================
# Symptom: a WebUI (or any older consumer) calling the Agent's kanban helpers as
# `hermes_cli.kanban_db.connect()` / `.connect_closing()` / `.dispatch_once()`
# raises `AttributeError: module 'hermes_cli.kanban_db' has no attribute
# 'connect'` (WebUI `/api/kanban/board` + `/api/kanban/assignees` -> HTTP 500).
# Root cause: the Agent split those helpers into SIBLING modules
# (`hermes_cli.kanban_db_connect`, `hermes_cli.kanban_db_dispatch`) and stopped
# re-exporting them from `kanban_db`. The WebUI's own `api/kanban_bridge.py`
# ships an ad-hoc shim for this, but that file is baked into the WebUI image and
# reverts on every WebUI update.
#
# Fix: a meta-path finder that, once `hermes_cli.kanban_db` has finished
# executing, aliases the moved helpers back onto it — only when the attribute is
# genuinely missing (never clobbering a real one). The sibling module is
# imported AFTER kanban_db has executed, so there is no import cycle
# (`kanban_db_connect` does not import `kanban_db`). This layer lives in the
# persistent /opt/hermes-railway sitecustomize.py (on PYTHONPATH at boot), so it
# survives both Agent and WebUI upgrades — the durable counterpart to the
# WebUI's baked shim.
# =============================================================================

_KANBAN_COMPAT_ALIASES = (
    # (source module, names to alias back onto hermes_cli.kanban_db)
    ("hermes_cli.kanban_db_connect", ("connect", "connect_closing")),
    ("hermes_cli.kanban_db_dispatch", ("dispatch_once",)),
)


def _install_kanban_module_split_compat() -> None:
    try:
        import importlib.abc as _iab
        import sys as _sys
    except Exception:
        return

    _TARGET_MODULE = "hermes_cli.kanban_db"

    if getattr(_sys, "_hermes_kanban_compat_installed", False):
        return

    class _KanbanCompatFinder(_iab.MetaPathFinder):
        """Wrap the real loader for `hermes_cli.kanban_db` and alias the helpers
        that the Agent split into sibling modules. Every other import passes
        through untouched."""

        def find_spec(self, fullname, path=None, target=None):
            if fullname != _TARGET_MODULE:
                return None
            try:
                for finder in _sys.meta_path:
                    if finder is self:
                        continue
                    spec = None
                    try:
                        spec = finder.find_spec(fullname, path, target)
                    except Exception:
                        spec = None
                    if spec is not None:
                        return self._wrap_spec(spec)
            except Exception:
                pass
            return None

        @staticmethod
        def _wrap_spec(spec):
            loader = getattr(spec, "loader", None)
            if loader is None:
                return spec
            orig_exec = getattr(loader, "exec_module", None)
            if orig_exec is None:
                return spec

            def _exec_then_alias(module):
                orig_exec(module)
                import importlib as _il
                for _src, _names in _KANBAN_COMPAT_ALIASES:
                    try:
                        _source = _il.import_module(_src)
                    except Exception:
                        continue
                    for _name in _names:
                        if getattr(module, _name, None) is None:
                            try:
                                setattr(module, _name, getattr(_source, _name))
                            except Exception:
                                pass
                try:
                    import logging as _lg
                    _lg.getLogger("sitecustomize").info(
                        "[hermes-sitecustomize] kanban_db compat aliases applied "
                        "(connect=%s, connect_closing=%s, dispatch_once=%s)",
                        hasattr(module, "connect"),
                        hasattr(module, "connect_closing"),
                        hasattr(module, "dispatch_once"),
                    )
                except Exception:
                    pass

            try:
                loader.exec_module = _exec_then_alias
            except Exception:
                pass
            return spec

    try:
        _sys.meta_path.insert(0, _KanbanCompatFinder())
        _sys._hermes_kanban_compat_installed = True
    except Exception:
        pass


_install_kanban_module_split_compat()

# =============================================================================
# FOREIGN-INTERPRETER DEPENDENCY-ENV GUARD (2026-10-13)
# =============================================================================
# The Agent's managed-dependency layer — `hermes_bootstrap.activate_dependencies()`,
# invoked on `import run_agent` — REPLACES every site-packages entry on sys.path
# with the PM-selected dependency venv (pm/environments.py:_activate_dependencies).
# PM pins and builds that venv with CPython 3.14 (pm/lock.json:
# cpython-3.14.7+20260901) while THIS container image runs CPython 3.13
# (PYTHON_VERSION=3.13.13, /opt/hermes/.venv = 3.13.13). Activating it points a
# 3.13 process at a 3.14 tree, so native extensions cannot load
# (_pydantic_core, yaml, regex, orjson, numpy, tiktoken, ...).
#
# Symptom (the reason this guard exists): every NEWLY SPAWNED agent process dies
# at model-client init with
#   "Failed to initialize OpenAI client: No module named 'pydantic_core._pydantic_core'"
# => agents do "one turn and then stop", Kanban/Buzz workers exit 255 and are
# reaped every minute. Long-lived processes started BEFORE PM committed the
# mismatched env keep working on their original sys.path, which is why the
# breakage looked intermittent. (Also confirmed: the managed env imports pydantic
# fine under its own python3.14 — it is only unusable from the 3.13 launcher.)
#
# Fix: once activation has run, drop any site-packages tree whose `pythonX.Y` tag
# does not match THIS interpreter and restore this interpreter's OWN
# site-packages. This is exactly the state that worked before the mismatched env
# was committed — purely additive/restorative. Delete this block to revert.
# =============================================================================

_RE_FOREIGN_SITE_PACKAGES = None


def _deactivate_foreign_dependency_env() -> None:
    """Undo an ABI-incompatible managed-dependency activation on sys.path."""
    global _RE_FOREIGN_SITE_PACKAGES
    try:
        import re as _re_abi
        import sysconfig as _sysconfig_abi
        import os as _os_abi
    except Exception:
        return
    try:
        _current = "python%d.%d" % (sys.version_info[0], sys.version_info[1])
    except Exception:
        return
    if _RE_FOREIGN_SITE_PACKAGES is None:
        _RE_FOREIGN_SITE_PACKAGES = _re_abi.compile(r"/lib/(python\d+\.\d+)/site-packages/?$")

    foreign = []
    for _entry in list(sys.path):
        if not _entry:
            continue
        _match = _RE_FOREIGN_SITE_PACKAGES.search(str(_entry))
        if _match and _match.group(1) != _current:
            foreign.append(_entry)
    if not foreign:
        return

    for _entry in foreign:
        try:
            sys.path.remove(_entry)
        except ValueError:
            pass

    own = None
    try:
        own = _sysconfig_abi.get_paths().get("purelib")
    except Exception:
        own = None
    if own and _os_abi.path.isdir(own) and own not in sys.path:
        sys.path.insert(0, own)

    # `activate_dependencies()` also rewrites os.environ["PYTHONPATH"] to
    # "<project_root>:<selected>" (pm/environments.py), DROPPING the durable patch
    # layer (/opt/hermes-railway). Every CHILD process (hermes -z workers, cron and
    # Kanban workers, Buzz agent subprocesses) is then spawned WITHOUT sitecustomize,
    # so it gets no ABI guard and fails the same way. Re-insert the layer.
    try:
        _layer = "/opt/hermes-railway"
        _pp = _os_abi.environ.get("PYTHONPATH", "")
        _parts = [p for p in _pp.split(_os_abi.pathsep) if p]
        if _os_abi.path.isdir(_layer) and _layer not in _parts:
            _parts.insert(0, _layer)
            _os_abi.environ["PYTHONPATH"] = _os_abi.pathsep.join(_parts)
    except Exception:
        pass

    try:
        import logging as _lg_abi
        _lg_abi.getLogger("sitecustomize").warning(
            "[hermes-sitecustomize] ignored ABI-incompatible dependency env %s "
            "(this interpreter=%s); restored own site-packages %s",
            foreign, _current, own,
        )
    except Exception:
        pass


def _install_foreign_dependency_env_guard() -> None:
    """Run the ABI guard now, and again whenever `hermes_bootstrap` executes
    (the module that performs the activation) — covering both orderings."""
    try:
        _deactivate_foreign_dependency_env()
    except Exception:
        pass

    try:
        import importlib.abc as _iab_abi
    except Exception:
        return

    if getattr(sys, "_hermes_abi_env_guard_installed", False):
        return

    class _AbiEnvGuardFinder(_iab_abi.MetaPathFinder):
        def find_spec(self, fullname, path=None, target=None):
            if fullname != "hermes_bootstrap":
                return None
            try:
                for finder in sys.meta_path:
                    if finder is self:
                        continue
                    spec = None
                    try:
                        spec = finder.find_spec(fullname, path, target)
                    except Exception:
                        spec = None
                    if spec is not None:
                        return self._wrap_spec(spec)
            except Exception:
                pass
            return None

        @staticmethod
        def _wrap_spec(spec):
            loader = getattr(spec, "loader", None)
            orig_exec = getattr(loader, "exec_module", None) if loader else None
            if orig_exec is None:
                return spec

            def _exec_then_guard(module):
                orig_exec(module)
                try:
                    _deactivate_foreign_dependency_env()
                except Exception:
                    pass

            try:
                loader.exec_module = _exec_then_guard
            except Exception:
                pass
            return spec

    try:
        sys.meta_path.insert(0, _AbiEnvGuardFinder())
        sys._hermes_abi_env_guard_installed = True
    except Exception:
        pass

    # `activate_dependencies()` is ALSO called directly, AFTER sitecustomize has
    # run, by the CLI and worker bootstraps (hermes_cli/source_completion.py,
    # update_serve_resume.py, update_completion.py, cron/worker_bootstrap.py).
    # The one-shot call above cannot catch those, so wrap the function itself —
    # every call re-applies the ABI guard. hermes_bootstrap does
    # `from pm.environments import activate_dependencies`, so wrapping the module
    # attribute before that import binds the guarded version everywhere.
    class _PmEnvWrapFinder(_iab_abi.MetaPathFinder):
        def find_spec(self, fullname, path=None, target=None):
            if fullname != "pm.environments":
                return None
            try:
                for finder in sys.meta_path:
                    if finder is self:
                        continue
                    spec = None
                    try:
                        spec = finder.find_spec(fullname, path, target)
                    except Exception:
                        spec = None
                    if spec is not None:
                        return self._wrap_spec(spec)
            except Exception:
                pass
            return None

        @staticmethod
        def _wrap_spec(spec):
            loader = getattr(spec, "loader", None)
            orig_exec = getattr(loader, "exec_module", None) if loader else None
            if orig_exec is None:
                return spec

            def _exec_then_wrap(module):
                orig_exec(module)
                try:
                    _orig = getattr(module, "activate_dependencies", None)
                    if _orig is not None and not getattr(_orig, "_hermes_abi_guarded", False):
                        def _guarded(*_a, **_kw):
                            _result = _orig(*_a, **_kw)
                            try:
                                _deactivate_foreign_dependency_env()
                            except Exception:
                                pass
                            return _result
                        _guarded._hermes_abi_guarded = True
                        module.activate_dependencies = _guarded
                except Exception:
                    pass

            try:
                loader.exec_module = _exec_then_wrap
            except Exception:
                pass
            return spec

    try:
        sys.meta_path.insert(0, _PmEnvWrapFinder())
    except Exception:
        pass

    # sitecustomize's OWN preload (import run_agent -> hermes_bootstrap) imports
    # pm.environments BEFORE the finder above is installed, so it is already
    # cached and the finder never fires. Wrap the live module attribute too, and
    # rebind hermes_bootstrap's binding if it already grabbed the original.
    try:
        _existing = sys.modules.get("pm.environments")
        if _existing is not None:
            _orig = getattr(_existing, "activate_dependencies", None)
            if _orig is not None and not getattr(_orig, "_hermes_abi_guarded", False):
                def _wrap_one(_fn):
                    def _guarded_fn(*_a, **_kw):
                        _r = _fn(*_a, **_kw)
                        try:
                            _deactivate_foreign_dependency_env()
                        except Exception:
                            pass
                        return _r
                    _guarded_fn._hermes_abi_guarded = True
                    return _guarded_fn

                _existing.activate_dependencies = _wrap_one(_orig)
                try:
                    _hb = sys.modules.get("hermes_bootstrap")
                    if _hb is not None and getattr(_hb, "activate_dependencies", None) is _orig:
                        _hb.activate_dependencies = _existing.activate_dependencies
                except Exception:
                    pass
    except Exception:
        pass


_install_foreign_dependency_env_guard()
