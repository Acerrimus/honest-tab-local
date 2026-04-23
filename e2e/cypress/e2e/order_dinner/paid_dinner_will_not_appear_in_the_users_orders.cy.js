import { getDataTestIdElement } from "../../helpers";
import {
  createUserOrderApi,
  generateOrderDetails,
  getUserOrdersApi,
} from "../../steps/orders";
import { getPaymentApi } from "../../steps/payments";
import {
  createGuestUserApi,
  generateUsername,
  logUserOn,
} from "../../steps/users";

describe("When a user pays for their dinner", { tags: "@payments" }, () => {
  it("the dinner does not appear in the user's orders", () => {
    const username = generateUsername();
    createGuestUserApi(username);
    cy.visit("/");
    logUserOn(username);
    getDataTestIdElement("dinner-signup-button").click();
    getDataTestIdElement("dinner-signup-pay-now").click();
    getDataTestIdElement("stripe_qr_code_image");
    cy.contains("Dinner sign-up registration successful!");
    getUserOrdersApi(username).then((response) => {
      expect(response.body.orders).to.have.lengthOf(1);
      const order = response.body.orders[0];
      expect(order.item).to.eq("Dinner sign-up");
      getPaymentApi(order.order_id).then((paymentResponse) => {
        expect(paymentResponse.body.payment.order_id).to.eq(order.order_id);
      });
    });
    const itemName = "REGISTERED TEST ITEM";
    const orderDetails = generateOrderDetails(username, itemName);
    createUserOrderApi(orderDetails);
    getDataTestIdElement("stripe_dialog_close").click();
    getDataTestIdElement("view-orders-button").click();
    getDataTestIdElement("ordered_item")
      .should("have.lengthOf", 1)
      .and("contain", itemName);
  });
});
