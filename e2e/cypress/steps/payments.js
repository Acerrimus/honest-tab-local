export function getStripeCheckoutSessionsApi(username) {
  return cy.request({
    url: "http://localhost:8000/api/test/stripe-checkout-sessions",
    qs: { username },
  });
}

export function getPaymentApi(order_id) {
  return cy.request({
    url: "http://localhost:8000/api/test/payments",
    qs: { order_id },
  });
}
