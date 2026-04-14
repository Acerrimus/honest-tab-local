import { getDataTestIdElement } from "../../helpers";
import {
  createUserOrderAPI,
  generateOrderDetails,
  getUserOrdersAPI,
} from "../../steps/orders";
import { getPaymentApi } from "../../steps/payments";
import {
  createGuestUserApi,
  generateUsername,
  logUserOn,
} from "../../steps/users";

describe("When a current guest successfully pays their tab and chooses to check out", () => {
  const username = generateUsername();
  it("they will no longer be seen on the login screen", () => {
    createGuestUserApi(username);
    const itemNames = [1, 2, 3].map((num) => `REGISTERED TEST ITEM${num}`);
    const orderDetails = itemNames.map((itemName) =>
      generateOrderDetails(username, itemName),
    );
    cy.wrap(orderDetails).each((orderDetail) => {
      createUserOrderAPI(orderDetail);
    });
    cy.visit("/");
    logUserOn(username);
    getDataTestIdElement("pay-tab-button").click();
    getDataTestIdElement("ordered_item").should("have.lengthOf", 3);
    getDataTestIdElement("total-amount-due").should(
      "have.text",
      "Total amount due: €3.00",
    );
    getDataTestIdElement("pay-tab-button").click();
    getDataTestIdElement("radio-input-yes").click();
    getDataTestIdElement("submit-button").click();
    getDataTestIdElement("stripe_qr_code_image");
    getDataTestIdElement("checkout-complete-text").should("be.visible");
    getDataTestIdElement("stripe_dialog_close").click();
    getDataTestIdElement("title").should("be.visible");
    cy.get(`[data-testid="user-button-${username}"]`).should("not.exist");
  });

  it("all their orders will have a paid status", () => {
    cy.waitUntil(() =>
      getUserOrdersAPI(username).then((response) => {
        cy.wrap(response.body.orders).each((order) => {
          getPaymentApi(order.order_id).then((paymentResponse) => {
            expect(paymentResponse.body.payment.order_id).to.eq(order.order_id);
          });
        });
      }),
    );
  });
});
