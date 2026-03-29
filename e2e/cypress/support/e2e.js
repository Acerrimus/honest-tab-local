import 'cypress-wait-until';

Cypress.on("uncaught:exception", (err, runnable) => {
  if (err.message.includes("Hydration failed")) {
    return false;
  }
});

Cypress.on("test:after:run", (result) => {
  if (result.state === "failed") {
    Cypress.runner.stop();
  }
});
