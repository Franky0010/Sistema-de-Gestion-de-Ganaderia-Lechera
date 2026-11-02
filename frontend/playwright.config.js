import { defineConfig } from '@playwright/test';
import { existsSync } from 'node:fs';
const chrome = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const edge = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
export default defineConfig({
  testDir: './tests/browser',
  fullyParallel: false,
  workers: 1,
  reporter: 'list',
  use: { baseURL: 'http://127.0.0.1:5173/ui/', viewport: {width:1440,height:1000}, launchOptions: { ...(existsSync(chrome)?{executablePath:chrome}:existsSync(edge)?{executablePath:edge}:{}) }, trace: 'retain-on-failure' },
  webServer: [
    {command:'npm run demo',url:'http://127.0.0.1:5173/ui/',reuseExistingServer:!process.env.CI},
    {command:'npm run dev -- --port 5174',url:'http://127.0.0.1:5174/ui/',reuseExistingServer:!process.env.CI},
  ],
});
