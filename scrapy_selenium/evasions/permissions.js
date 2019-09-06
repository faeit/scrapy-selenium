const originalQuery = window.navigator.permissions.query
window.navigator.permissions.__proto__.query = (parameters) =>
(parameters.name === 'notifications'?Promise.resolve({ state: Notification.permission }):originalQuery(parameters))