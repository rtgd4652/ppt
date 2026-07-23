const readline = require("node:readline");
const { BrowserManager } = require("../../crawler/src/browser-manager");

const targetUrl = process.argv[2];
const requestedSeconds = process.argv
  .slice(3)
  .map((value) => Number(value))
  .filter((value) => Number.isFinite(value));

if (!targetUrl) {
  console.error("缺少视频页面地址。");
  process.exit(1);
}

async function seekAndCapture(browser, targetSecond) {
  // 只在页面内定位时间点，不读取字幕，也不下载视频资源。
  await browser.page.evaluate(async (target) => {
    const video = document.querySelector("video");
    video.pause();

    if (Math.abs(video.currentTime - target) > 0.5) {
      await new Promise((resolve) => {
        let finished = false;
        const done = () => {
          if (!finished) {
            finished = true;
            resolve();
          }
        };

        video.addEventListener("seeked", done, { once: true });
        video.currentTime = target;
        setTimeout(done, 3000);
      });
    }

    video.pause();
  }, targetSecond);

  // 等待目标帧真正进入可渲染状态，避免只截到播放器黑屏占位。
  await browser.page
    .waitForFunction(
      (target) => {
        const video = document.querySelector("video");
        return (
          video &&
          video.readyState >= 2 &&
          Math.abs(video.currentTime - target) <= 1
        );
      },
      targetSecond,
      { timeout: 5000 }
    )
    .catch(() => {});
  await browser.page.waitForTimeout(800);

  const actualSecond = await browser.page.evaluate(
    () => document.querySelector("video").currentTime
  );
  const videoRect = await browser.page.locator("video").boundingBox();

  // 截图仅保存在内存 Buffer 中，通过标准输出交给当前审核会话。
  const imageBuffer = await browser.page.screenshot({
    type: "jpeg",
    quality: 36,
    clip: videoRect,
  });

  return {
    target: targetSecond,
    actual: actualSecond,
    image: imageBuffer.toString("base64"),
  };
}

async function main() {
  const browser = new BrowserManager({
    headless: true,
    viewport: { width: 960, height: 600 },
    timeout: 120_000,
  });

  try {
    await browser.start();
    await browser.goto(targetUrl);
    await browser.page.waitForSelector("video", { timeout: 120_000 });
    await browser.page.waitForFunction(
      () => {
        const video = document.querySelector("video");
        return video && Number.isFinite(video.duration) && video.duration > 0;
      },
      null,
      { timeout: 120_000 }
    );
    await browser.page.evaluate(() => document.querySelector("video").pause());

    const metadata = await browser.page.evaluate(() => {
      const video = document.querySelector("video");
      return {
        title: document.title,
        duration: video.duration,
        currentTime: video.currentTime,
        paused: video.paused,
      };
    });

    console.log(`__READY__${JSON.stringify(metadata)}`);

    // 传入时间点参数时采用一次性批量模式，适合不落盘的自动抽样。
    if (requestedSeconds.length > 0) {
      for (const targetSecond of requestedSeconds) {
        const frame = await seekAndCapture(browser, targetSecond);
        console.log(`__FRAME__${JSON.stringify(frame)}`);
      }
      return;
    }

    const input = readline.createInterface({ input: process.stdin });
    for await (const line of input) {
      const value = line.trim();
      if (value === "quit") {
        break;
      }

      const targetSecond = Number(value);
      if (!Number.isFinite(targetSecond)) {
        console.log("__ERROR__无效时间点");
        continue;
      }

      try {
        const frame = await seekAndCapture(browser, targetSecond);
        console.log(`__FRAME__${JSON.stringify(frame)}`);
      } catch (error) {
        console.log(`__ERROR__${error.message}`);
      }
    }
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
