import { getDataTestIdElement } from "../../helpers";
import {
  createUserOrderApi,
  generateOrderDetails,
  getUserOrdersApi,
} from "../../steps/orders";
import { getPaymentApi } from "../../steps/payments";
import {
  assertStripeLineItemsMatchExpected,
  triggerSuccessfulStripePayment,
} from "../../steps/stripe";
import {
  createGuestUserApi,
  generateUsername,
  logUserOn,
} from "../../steps/users";

describe(
  "When a user pays for their dinner",
  { testIsolation: false, tags: "@payments" },
  () => {
    it("the dinner does not appear in the user's orders", () => {
      const username = generateUsername();
      createGuestUserApi(username);
      cy.visit("/");
      logUserOn(username);
      getDataTestIdElement("dinner-signup-button").click();
      getDataTestIdElement("dinner-signup-pay-now").click();
      getDataTestIdElement("stripe_qr_code_image");
      getDataTestIdElement("stripe-subtotal").should(
        "have.text",
        "Subtotal: €12.00",
      );
      getDataTestIdElement("stripe-handling-fee").should(
        "have.text",
        "System Provider Handling Fee: €0.39",
      );
      getDataTestIdElement("stripe-total").should("have.text", "Total: €12.39");

      triggerSuccessfulStripePayment();
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

    it("will record the line items correctly for Stripe", () => {
      assertStripeLineItemsMatchExpected([
        {
          price_data: {
            currency: "eur",
            product_data: { name: "Dinner sign-up" },
            unit_amount: 1200,
          },
          quantity: 1,
        },
        {
          price_data: {
            currency: "eur",
            product_data: { name: "System Provider Handling Fee" },
            unit_amount: 39,
          },
          quantity: 1,
        },
      ]);
    });
  },
);
