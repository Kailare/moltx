import { CLAUDE_CLI_PROFILE_ID, CODEX_CLI_PROFILE_ID } from "../agents/auth-profiles.js";
import { colorize, isRich, theme } from "../terminal/theme.js";
// GrokClaw: Stripped to xAI-only. Original imports kept for compatibility.
const AUTH_CHOICE_GROUP_DEFS = [
    {
        value: "xai",
        label: "xAI",
        hint: "Grok API key",
        choices: ["xai-api-key"],
    },
];
function formatOAuthHint(expires, opts) {
    const rich = isRich();
    if (!expires) {
        return colorize(rich, theme.muted, "token unavailable");
    }
    const now = Date.now();
    const remaining = expires - now;
    if (remaining <= 0) {
        if (opts?.allowStale) {
            return colorize(rich, theme.warn, "token present · refresh on use");
        }
        return colorize(rich, theme.error, "token expired");
    }
    const minutes = Math.round(remaining / (60 * 1000));
    const duration = minutes >= 120
        ? `${Math.round(minutes / 60)}h`
        : minutes >= 60
            ? "1h"
            : `${Math.max(minutes, 1)}m`;
    const label = `token ok · expires in ${duration}`;
    if (minutes <= 10) {
        return colorize(rich, theme.warn, label);
    }
    return colorize(rich, theme.success, label);
}
export function buildAuthChoiceOptions(params) {
    const options = [];
    options.push({
        value: "xai-api-key",
        label: "xAI Grok API key",
        hint: "Get your key at console.x.ai",
    });
    if (params.includeSkip) {
        options.push({ value: "skip", label: "Skip for now" });
    }
    return options;
}
export function buildAuthChoiceGroups(params) {
    const options = buildAuthChoiceOptions({
        ...params,
        includeSkip: false,
    });
    const optionByValue = new Map(options.map((opt) => [opt.value, opt]));
    const groups = AUTH_CHOICE_GROUP_DEFS.map((group) => ({
        ...group,
        options: group.choices
            .map((choice) => optionByValue.get(choice))
            .filter((opt) => Boolean(opt)),
    }));
    const skipOption = params.includeSkip
        ? { value: "skip", label: "Skip for now" }
        : undefined;
    return { groups, skipOption };
}
