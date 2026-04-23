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

// export function getStripeLineItems() {
//   return cy.getAllSessionStorage().then((result) =>
//     cy.request({
//       url: "http://app:8000/api/test/stripe/line-items",
//       qs: {
//         token: result["http://app:3000"].token,
//       },
//     }),
//   );
// }

function sortLineItemsByItemName(lineItems) {
  return lineItems.sort((a, b) =>
    a.price_data.product_data.name.localeCompare(
      b.price_data.product_data.name,
    ),
  );
}

export function assertStripeLineItemsMatchExpected(expectedLineItems) {
  cy.getAllSessionStorage()
    .then((result) =>
      cy.request({
        url: "http://app:8000/api/test/stripe/line-items",
        qs: {
          token: result["http://app:3000"].token,
        },
      }),
    )
    .then((result) => {
      expect(sortLineItemsByItemName(result.body.line_items)).to.deep.equal(
        sortLineItemsByItemName(expectedLineItems),
      );
    });
}
