const WebSocket = globalThis.WebSocket;

/**
 * Google Flow Automation via Chrome DevTools Protocol (CDP)
 * Connects to the running Chrome instance with remote debugging on port 9222.
 */
class GoogleFlowClient {
  constructor(port = 9222) {
    this.port = port;
    this.pageWs = null;
  }

  async getFlowTarget() {
    const res = await fetch(`http://localhost:${this.port}/json`);
    const targets = await res.json();
    return targets.find(t => t.url && t.url.includes('flow.google.com'));
  }

  async connect() {
    const target = await this.getFlowTarget();
    if (!target) {
      throw new Error('No open flow.google.com tab found in Chrome on port ' + this.port);
    }
    this.pageWs = new WebSocket(target.webSocketDebuggerUrl);
    await new Promise((resolve, reject) => {
      this.pageWs.onopen = resolve;
      this.pageWs.onerror = reject;
    });
  }

  evaluate(expr) {
    return new Promise((resolve, reject) => {
      const id = Math.floor(Math.random() * 1000000);
      const handler = (msg) => {
        const res = JSON.parse(msg.data);
        if (res.id === id) {
          this.pageWs.removeEventListener('message', handler);
          if (res.error) reject(res.error);
          else resolve(res.result?.result?.value);
        }
      };
      this.pageWs.addEventListener('message', handler);
      this.pageWs.send(JSON.stringify({
        id,
        method: 'Runtime.evaluate',
        params: { expression: expr, returnByValue: true }
      }));
    });
  }

  sendCDP(method, params) {
    return new Promise((resolve, reject) => {
      const id = Math.floor(Math.random() * 1000000);
      const handler = (msg) => {
        const res = JSON.parse(msg.data);
        if (res.id === id) {
          this.pageWs.removeEventListener('message', handler);
          if (res.error) reject(res.error);
          else resolve(res.result);
        }
      };
      this.pageWs.addEventListener('message', handler);
      this.pageWs.send(JSON.stringify({ id, method, params }));
    });
  }

  async insertPromptAndGenerate(promptText) {
    console.log(`[Flow] Setting prompt: "${promptText.substring(0, 50)}..."`);
    
    // Insert text into contenteditable box via execCommand
    const boxReady = await this.evaluate(`(() => {
      const box = document.querySelector('div[aria-label="¿Qué quieres crear?"]');
      if (!box) return false;
      box.focus();
      document.execCommand("selectAll", false, null);
      document.execCommand("insertText", false, ${JSON.stringify(promptText)});
      return true;
    })()`);

    if (!boxReady) {
      throw new Error('Prompt input element not found in Google Flow.');
    }

    // Get coordinates for the submit button to dispatch trusted click
    const rect = await this.evaluate(`(() => {
      const btn = Array.from(document.querySelectorAll("button")).find(b => b.getAttribute("aria-label") === "Iniciar generación");
      if (!btn) return null;
      const r = btn.getBoundingClientRect();
      return { x: r.left + r.width / 2, y: r.top + r.height / 2 };
    })()`);

    if (!rect) {
      throw new Error('Iniciar generación button not found.');
    }

    // Dispatch trusted mouse click
    await this.sendCDP('Input.dispatchMouseEvent', {
      type: 'mousePressed',
      x: rect.x,
      y: rect.y,
      button: 'left',
      clickCount: 1
    });
    await this.sendCDP('Input.dispatchMouseEvent', {
      type: 'mouseReleased',
      x: rect.x,
      y: rect.y,
      button: 'left',
      clickCount: 1
    });

    console.log('[Flow] Generation triggered successfully.');
  }

  async waitForCompletion(timeoutMs = 120000) {
    const startTime = Date.now();
    while (Date.now() - startTime < timeoutMs) {
      const status = await this.evaluate(`(() => {
        const text = document.body.innerText;
        const match = text.match(/(\\d+)%/);
        const percent = match ? parseInt(match[1], 10) : null;
        const imgs = Array.from(document.querySelectorAll("img, video")).map(i => i.src).filter(s => s && s.includes("flow.google.com/asb/"));
        return { percent, finished: !match && imgs.length > 0, mediaUrls: imgs };
      })()`);

      if (status.percent) {
        process.stdout.write(`\\r[Flow] Progress: ${status.percent}%`);
      } else if (status.finished) {
        console.log('\\n[Flow] Generation complete!');
        return status.mediaUrls;
      }
      await new Promise(r => setTimeout(r, 2500));
    }
    throw new Error('Timed out waiting for Flow generation.');
  }

  close() {
    if (this.pageWs) this.pageWs.close();
  }
}

module.exports = GoogleFlowClient;

if (require.main === module) {
  const prompt = process.argv[2] || "Vertical 9:16 cinematic extreme macro shot of an automotive brake disc spinning on a heavy lathe machine in a workshop, sparks flying, photorealistic 4k";
  const client = new GoogleFlowClient();
  client.connect()
    .then(() => client.insertPromptAndGenerate(prompt))
    .then(() => client.waitForCompletion())
    .then((urls) => {
      console.log('Generated Media URLs:', urls);
      client.close();
    })
    .catch((err) => {
      console.error(err);
      client.close();
      process.exit(1);
    });
}
