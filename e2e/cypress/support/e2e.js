Cypress.on('uncaught:exception', (err, runnable) => {
  if (err.message.includes('Hydration failed')) {
    return false
  }
})