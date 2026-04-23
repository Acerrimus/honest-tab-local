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
  "When a user pays for their breakfast",
  { testIsolation: false, tags: "@payments" },
  () => {
    it("the breakfast does not appear in the user's orders", () => {
      const username = generateUsername();
      createGuestUserApi(username);
      cy.visit("/");
      logUserOn(username);
      getDataTestIdElement("breakfast-signup-button").click();
      getDataTestIdElement("breakfast-signup-item-select").click();
      getDataTestIdElement("breakfast-signup-item-option").first().click();
      getDataTestIdElement("breakfast-pay-now").click();
      getDataTestIdElement("stripe-subtotal").should(
        "have.text",
        "Subtotal: €8.00",
      );
      getDataTestIdElement("stripe-handling-fee").should(
        "have.text",
        "System Provider Handling Fee: €0.26",
      );
      getDataTestIdElement("stripe-total").should("have.text", "Total: €8.26");
      getDataTestIdElement("stripe_qr_code_image");
      triggerSuccessfulStripePayment();
      cy.contains("Breakfast sign-up registration successful!");
      getUserOrdersApi(username).then((response) => {
        expect(response.body.orders).to.have.lengthOf(1);
        const order = response.body.orders[0];
        expect(order.item).to.eq("Breakfast sign-up");
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
            product_data: {
              name: "Vegan (Breakfast sign-up)",
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
    });
  },
);
