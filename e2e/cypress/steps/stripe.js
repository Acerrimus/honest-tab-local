export function assertStripeDialogNotVisibleBeforeItemPayButton() {
  cy.waitUntil(
    () => {
      if (Cypress.$('[data-testid="stripe_dialog_title"]').length) {
        throw new Error("Stripe dialog should not be visible");
      }
      return Cypress.$('[data-testid="item_pay_now"]').length;
    },
    { timeout: 20000, errorMsg: "Item pay button should be visible" },
  );
}

export function triggerSuccessfulStripePayment() {
  cy.getAllSessionStorage().then((result) => {
    cy.request({
      method: "POST",
      url: "http://app:8000/api/test/stripe/trigger",
      qs: {
        stripe_test_state: "success",
        token: result["http://app:3000"].token,
      },
    });
  });
}
