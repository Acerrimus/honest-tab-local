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
      url: "http://localhost:8000/api/test/stripe/trigger",
      qs: {
        stripe_test_state: "success",
        token: result["http://localhost:3000"].token,
      },
    });
  });
}

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
        url: "http://localhost:8000/api/test/stripe/line-items",
        qs: {
          token: result["http://localhost:3000"].token,
        },
      }),
    )
    .then((result) => {
      expect(sortLineItemsByItemName(result.body.line_items)).to.deep.equal(
        sortLineItemsByItemName(expectedLineItems),
      );
    });
}

export function assertBreakfastLineItemsMatchExpected() {
  assertStripeLineItemsMatchExpected([
    {
      price_data: {
        currency: "eur",
        product_data: {
          name: "Breakfast sign-up (Vegan)",
        },
        unit_amount: 800,
      },
      quantity: 1,
    },
    {
      price_data: {
        currency: "eur",
        product_data: {
          name: "System Provider Handling Fee",
        },
        unit_amount: 26,
      },
      quantity: 1,
    },
  ]);
}
