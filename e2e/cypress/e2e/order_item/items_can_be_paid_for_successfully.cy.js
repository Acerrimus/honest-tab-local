import { getDataTestIdElement } from "../../helpers";
import {
  createUserOrderApi,
  generateOrderDetails,
  getUserOrdersApi,
} from "../../steps/orders";
import {
  getPaymentApi,
  getStripeCheckoutSessionsApi,
} from "../../steps/payments";
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
  "When a user pays for an item",
  { testIsolation: false, tags: "@payments" },
  () => {
    it("will showm with the correct total, the item will be registered but not appear in the user's orders", () => {
      const username = generateUsername();
      createGuestUserApi(username);
      cy.visit("/");
      logUserOn(username);
      getDataTestIdElement("order_item_button")
        .filter(":contains(TEST ITEM (€1.00))")
        .click();
      getDataTestIdElement("item_pay_now").click();
      getDataTestIdElement("stripe-subtotal").should(
        "have.text",
        "Subtotal: €1.00",
      );
      getDataTestIdElement("stripe-handling-fee").should(
        "have.text",
        "System Provider Handling Fee: €0.03",
      );
      getDataTestIdElement("stripe-total").should("have.text", "Total: €1.03");
      getDataTestIdElement("stripe_qr_code_image");
      triggerSuccessfulStripePayment();
      getDataTestIdElement("stripe_payment_successful_text").should(
        "be.visible",
      );
      cy.contains("'TEST ITEM' registered succesfully. Thank you!");
      getUserOrdersApi(username).then((userOrdersresponse) => {
        expect(userOrdersresponse.body.orders).to.have.lengthOf(1);
        const order = userOrdersresponse.body.orders[0];
        expect(order.item).to.eq("TEST ITEM");
        getStripeCheckoutSessionsApi(username).then(
          (stripeCheckoutSessionsResponse) => {
            expect(
              stripeCheckoutSessionsResponse.body.checkout_sessions,
            ).to.have.lengthOf(1);
            expect(
              stripeCheckoutSessionsResponse.body.checkout_sessions[0].order_id,
            ).to.eq(order.order_id);
            expect(
              stripeCheckoutSessionsResponse.body.checkout_sessions[0].user,
            ).to.eq(username);
          },
        );
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
              name: "TEST ITEM",
            },
            unit_amount: 100,
          },
          quantity: 1,
        },
        {
          price_data: {
            currency: "eur",
            product_data: {
              name: "System Provider Handling Fee",
            },
            unit_amount: 3,
          },
          quantity: 1,
        },
      ]);
    });
  },
);
