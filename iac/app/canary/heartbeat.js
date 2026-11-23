const synthetics = require('Synthetics');

const checkPage = async (page, name, url) => {
  await synthetics.executeStep(name, async () => {
    const response = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
    const status = response ? response.status() : 0;
    if (status < 200 || status > 299) {
      throw new Error(`${url} returned status ${status}`);
    }
  });
};

exports.handler = async () => {
  const baseUrl = process.env.TCF_SITE_URL || 'https://thecourseforum.com';
  const siteOrigin = new URL(baseUrl).origin;
  const page = await synthetics.getPage();
  await page.setRequestInterception(true);
  page.on('request', (request) => {
    if (request.isInterceptResolutionHandled()) {
      return;
    }
    if (new URL(request.url()).origin !== siteOrigin) {
      request.continue();
      return;
    }
    request.continue({
      headers: { ...request.headers(), 'x-tcf-canary': process.env.TCF_CANARY_SECRET || '' },
    });
  });
  await checkPage(page, 'home', `${baseUrl}/`);
  await checkPage(page, 'browse', `${baseUrl}/browse/`);
};
