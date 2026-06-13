// BunuDaBastık3D Google Forms -> Cloud Bridge
// Sheet bağlı formda Apps Script içine yapıştır.
// Trigger: onFormSubmit, event type: On form submit

const BRIDGE_URL = 'https://SENIN-DOMAININ.com/webhook/google-forms';
const BDB_SECRET = ''; // Cloud Bridge BDB_WEBHOOK_SECRET kullandıysan buraya yaz.

function onFormSubmit(e) {
  const named = e.namedValues || {};
  const payload = {};

  Object.keys(named).forEach(function(key) {
    const value = named[key];
    payload[key] = Array.isArray(value) ? value.join(', ') : value;
  });

  payload.timestamp = new Date().toISOString();
  payload.response_id = Utilities.getUuid();

  const options = {
    method: 'post',
    contentType: 'application/json',
    payload: JSON.stringify(payload),
    muteHttpExceptions: true,
    headers: {}
  };

  if (BDB_SECRET) {
    options.headers['x-bdb-secret'] = BDB_SECRET;
  }

  const response = UrlFetchApp.fetch(BRIDGE_URL, options);
  Logger.log(response.getResponseCode() + ' ' + response.getContentText());
}
