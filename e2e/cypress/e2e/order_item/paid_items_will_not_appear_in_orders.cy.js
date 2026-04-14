import { getDataTestIdElement } from "../../helpers";
import {
  createUserOrderAPI,
  generateOrderDetails,
  getUserOrdersAPI,
} from "../../steps/orders";
import { getPaymentApi, getStripeCheckoutSessionsApi } from "../../steps/payments";
import {
  createGuestUserApi,
  generateUsername,
  logUserOn,
} from "../../steps/users";

describe("When a user pays for an item", () => {
  it("the item will be registered but not appear in the user's orders", () => {
    const username = generateUsername();
    createGuestUserApi(username);
    cy.visit("/");
    logUserOn(username);
    getDataTestIdElement("order_item_button")
      .filter(":contains(TEST ITEM (€1.00))")
      .click();
    getDataTestIdElement("item_pay_now").click();
    getDataTestIdElement("stripe_qr_code_image");
    getDataTestIdElement("stripe_payment_successful_text").should("be.visible");
    cy.contains("'TEST ITEM' registered succesfully. Thank you!");
    getUserOrdersAPI(username).then((userOrdersresponse) => {
      expect(userOrdersresponse.body.orders).to.have.lengthOf(1);
      const order = userOrdersresponse.body.orders[0];
      expect(order.item).to.eq("TEST ITEM");
      getStripeCheckoutSessionsApi(username).then(
        (stripeCheckoutSessionsResponse) => {
          expect(stripeCheckoutSessionsResponse.body.checkout_sessions).to.have.lengthOf(
            1,
          );
          expect(
            stripeCheckoutSessionsResponse.body.checkout_sessions[0].order_id,
          ).to.eq(order.order_id);
          expect(stripeCheckoutSessionsResponse.body.checkout_sessions[0].user).to.eq(
            username,
          );
        },
      );
      getPaymentApi(order.order_id).then(paymentResponse => {
        expect(paymentResponse.body.payment.order_id).to.eq(order.order_id)
      })
    });
    const itemName = "REGISTERED TEST ITEM";
    const orderDetails = generateOrderDetails(username, itemName);
    createUserOrderAPI(orderDetails);
    getDataTestIdElement("stripe_dialog_close").click();
    getDataTestIdElement("view-orders-button").click();
    getDataTestIdElement("ordered_item")
      .should("have.lengthOf", 1)
      .and("contain", itemName);
  });
});
