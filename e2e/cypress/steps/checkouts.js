export function getCheckoutApi(username) {
  return cy.request({
    url: "http://app:8000/api/test/checkout",
    qs: { username },
  });
}