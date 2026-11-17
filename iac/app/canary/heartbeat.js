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
  const page = await synthetics.getPage();
  await page.setExtraHTTPHeaders({ 'x-tcf-canary': process.env.TCF_CANARY_SECRET || '' });
  await checkPage(page, 'home', `${baseUrl}/`);
  await checkPage(page, 'browse', `${baseUrl}/browse/`);
};
