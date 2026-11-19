/**
 * Playwright MCP regression checks for asynchronous event-dialog focus.
 * Run this file with browser_run_code_unsafe's filename argument against the
 * local site on port 8000 after loading the November 2026 sample events.
 */
// eslint-disable-next-line no-unused-vars -- Playwright MCP evaluates this function.
async function testClubEventsFocus(page) {
  const base =
    "http://127.0.0.1:8000/club-events/?mode=clubs&from=2026-11-01&to=2026-11-30";
  const listPattern = /club-events\/\?.*partial=results/;
  const detailPattern = /club-events\/\d+\/\?.*partial=details/;
  const passed = [];
  const failed = [];

  /** Fail a check with a descriptive message rather than an opaque count. */
  function assert(condition, message) {
    if (!condition) throw new Error(message);
  }

  /** Create an explicit network gate so each focus race is reproducible. */
  function gate() {
    let release;
    const promise = new Promise((resolve) => {
      release = resolve;
    });
    return { promise, release };
  }

  /** Run an independent browser case and collect its failure for the report. */
  async function check(name, run) {
    try {
      await page.goto(base);
      await page.locator(".event-row").first().waitFor();
      await run();
      passed.push(name);
    } catch (error) {
      failed.push(`${name}: ${error.message}`);
    } finally {
      await page.unroute(listPattern);
      await page.unroute(detailPattern);
    }
  }

  await page.route(
    /googlesyndication\.com|googletagmanager\.com|sdk\.awswaf\.com/,
    (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/javascript",
        body: "",
      }),
  );
  await page.setViewportSize({ width: 1440, height: 1000 });

  await check("list response preserves open modal focus", async () => {
    const responseReady = gate();
    const delivered = gate();
    await page.route(listPattern, async (route) => {
      const response = await route.fetch();
      await responseReady.promise;
      await route.fulfill({ response });
      delivered.release();
    });
    try {
      await page
        .getByLabel("Search events", { exact: true })
        .fill("Open House");
      await page.getByRole("button", { name: "Apply", exact: true }).click();
      await page.locator('#eventResults[aria-busy="true"]').waitFor();
      // Busy results reject pointer input but remain reachable by keyboard.
      const trigger = page.locator(".event-row [data-event-detail]").first();
      await trigger.focus();
      await page.keyboard.press("Enter");
      const close = page.getByRole("button", { name: "Close event details" });
      // Do not let the initial modal-open timer mask the response's focus theft.
      await page.waitForTimeout(150);
      await close.focus();
      responseReady.release();
      await delivered.promise;
      // Allow the response's DOM update and the shared focus timer to run.
      await page.waitForTimeout(200);
      assert(
        await page
          .locator("#clubEventModal")
          .evaluate((dialog) => dialog.contains(document.activeElement)),
        "The list response moved focus outside the modal.",
      );
      await page.keyboard.press("Tab");
      assert(
        await page
          .locator("#clubEventModal")
          .evaluate((dialog) => dialog.contains(document.activeElement)),
        "Tab escaped the open modal.",
      );
      await page.keyboard.press("Escape");
      await page.waitForFunction(() => {
        const results = document.getElementById("eventResults");
        return (
          !results.hasAttribute("aria-busy") &&
          results === document.activeElement
        );
      });
      assert(
        (await page.locator(".event-row").count()) === 1,
        "List update was lost.",
      );
    } finally {
      responseReady.release();
    }
  });

  await check(
    "details retry retains focus through loading and success",
    async () => {
      await page.route(detailPattern, (route) =>
        route.fulfill({ status: 503, body: "Temporarily unavailable" }),
      );
      const trigger = page.locator(".event-row [data-event-detail]").first();
      await trigger.focus();
      await page.keyboard.press("Enter");
      const retry = page
        .locator("#clubEventModal")
        .getByRole("button", { name: "Try again" });
      await retry.waitFor();
      // Wait until the initial modal-open focus timer has already fired.
      await page.waitForTimeout(150);
      await page.unroute(detailPattern);
      const responseReady = gate();
      await page.route(detailPattern, async (route) => {
        const response = await route.fetch();
        await responseReady.promise;
        await route.fulfill({ response });
      });
      try {
        await retry.focus();
        await page.keyboard.press("Enter");
        await page.getByText("Loading event…", { exact: true }).waitFor();
        assert(
          await page
            .getByRole("button", { name: "Close event details" })
            .evaluate((button) => button === document.activeElement),
          "Replacing the Retry button lost focus instead of moving it to Close.",
        );
        responseReady.release();
        await page
          .locator("#clubEventTitle")
          .filter({ hasText: "Open House" })
          .waitFor();
        assert(
          await page
            .locator("#clubEventModal")
            .evaluate((dialog) => dialog.contains(document.activeElement)),
          "The successful retry lost modal focus.",
        );
        await page.keyboard.press("Escape");
        assert(
          await trigger.evaluate((link) => link === document.activeElement),
          "Closing the modal did not restore its trigger.",
        );
      } finally {
        responseReady.release();
      }
    },
  );

  await check("ordinary list updates still focus results", async () => {
    await page.getByLabel("Search events", { exact: true }).fill("Open House");
    await page.getByRole("button", { name: "Apply", exact: true }).click();
    await page.waitForFunction(() => {
      const results = document.getElementById("eventResults");
      return (
        !results.hasAttribute("aria-busy") && results === document.activeElement
      );
    });
    assert(
      (await page.locator(".event-row").count()) === 1,
      "Filtering failed.",
    );
  });

  if (failed.length) throw new Error(failed.join("\n"));
  return { passed };
}
