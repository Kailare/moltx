#!/usr/bin/env node
/**
 * Patches the upstream models.generated.js to fix xAI/Grok model routing.
 * 
 * Problem: Upstream routes xai/grok-3 through Vercel AI Gateway with
 * anthropic-messages API, which breaks tool calling.
 * 
 * Fix: Route directly to api.x.ai/v1 with openai-completions API.
 */

import { readFileSync, writeFileSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const modelsPath = resolve(__dirname, '../node_modules/@mariozechner/pi-ai/dist/models.generated.js');

try {
    let content = readFileSync(modelsPath, 'utf8');
    let patched = false;

    // Patch grok-3
    const grok3Old = `"xai/grok-3": {
            id: "xai/grok-3",
            name: "Grok 3 Beta",
            api: "anthropic-messages",
            provider: "vercel-ai-gateway",
            baseUrl: "https://ai-gateway.vercel.sh",`;
    
    const grok3New = `"xai/grok-3": {
            id: "xai/grok-3",
            name: "Grok 3",
            api: "openai-completions",
            provider: "xai",
            baseUrl: "https://api.x.ai/v1",`;

    if (content.includes(grok3Old)) {
        content = content.replace(grok3Old, grok3New);
        patched = true;
    }

    // Patch grok-3-mini
    const grok3MiniOld = `"xai/grok-3-mini": {
            id: "xai/grok-3-mini",
            name: "Grok 3 Mini Beta",
            api: "anthropic-messages",
            provider: "vercel-ai-gateway",
            baseUrl: "https://ai-gateway.vercel.sh",`;
    
    const grok3MiniNew = `"xai/grok-3-mini": {
            id: "xai/grok-3-mini",
            name: "Grok 3 Mini",
            api: "openai-completions",
            provider: "xai",
            baseUrl: "https://api.x.ai/v1",`;

    if (content.includes(grok3MiniOld)) {
        content = content.replace(grok3MiniOld, grok3MiniNew);
        patched = true;
    }

    if (patched) {
        writeFileSync(modelsPath, content);
        console.log('✅ Patched xAI model routing (openai-completions → api.x.ai)');
    } else {
        console.log('ℹ️  Models already patched or format changed — skipping');
    }
} catch (err) {
    console.error('⚠️  Could not patch models:', err.message);
}
