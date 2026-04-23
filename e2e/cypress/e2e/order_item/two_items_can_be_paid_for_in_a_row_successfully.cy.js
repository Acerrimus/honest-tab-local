import { getDataTestIdElement } from "../../helpers";
import { getUserOrdersApi } from "../../steps/orders";
import { getPaymentApi } from "../../steps/payments";
import { triggerSuccessfulStripePayment } from "../../steps/stripe";
import {
  createGuestUserApi,
  generateUsername,
  logUserOn,
} from "../../steps/users";

describe(
  "When a user pays for two items in a row",
  { tags: "@payments" },
  () => {
    it("the items will be successfully paid for", () => {
      const username = generateUsername();
      createGuestUserApi(username);
      cy.visit("/");
      logUserOn(username);
      getDataTestIdElement("order_item_button")
        .filter(":contains(TEST ITEM (€1.00))")
        .click();
      getDataTestIdElement("item_pay_now").click();
      getDataTestIdElement("stripe_qr_code_image");
      triggerSuccessfulStripePayment();
      getDataTestIdElement("stripe_payment_successful_text").should(
        "be.visible",
      );
      cy.contains("'TEST ITEM' registered succesfully. Thank you!");
      getDataTestIdElement("stripe_dialog_close").click();
      getDataTestIdElement("order_item_button")
        .filter(":contains(TEST ITEM (€1.00))")
        .click();
      getDataTestIdElement("item_pay_now").click();
      getDataTestIdElement("stripe_qr_code_image");
      triggerSuccessfulStripePayment();
      getDataTestIdElement("stripe_payment_successful_text").should(
        "be.visible",
      );
      cy.contains("'TEST ITEM' registered succesfully. Thank you!");
      cy.waitUntil(() =>
        getUserOrdersApi(username).then((response) => {
          cy.wrap(response.body.orders).each((order) => {
            getPaymentApi(order.order_id).then((paymentResponse) => {
              expect(paymentResponse.body.payment.order_id).to.eq(
                order.order_id,
              );
            });
          });
        }),
      );
    });
  },
);
