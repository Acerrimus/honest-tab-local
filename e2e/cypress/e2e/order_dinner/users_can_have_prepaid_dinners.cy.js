import { getDataTestIdElement } from "../../helpers";
import {
  assertStripeLineItemsMatchExpected,
  triggerSuccessfulStripePayment,
} from "../../steps/stripe";
import {
  createGuestUserWithPrepaidDinnersApi,
  generateUsername,
  logUserOn,
} from "../../steps/users";

describe(
  "When a user has prepaid dinners",
  { testIsolation: false, tags: ["@smoke", "@prepaidDinner"] },
  () => {
    const username = generateUsername();

    before(() => {
      createGuestUserWithPrepaidDinnersApi(username, 2);
    });

    it("they will see the number of prepaid dinners displayed when they go to order dinner", () => {
      cy.visit("/");
      logUserOn(username);
      getDataTestIdElement("dinner-signup-button").click();
      getDataTestIdElement("prepaid-dinners-message").should(
        "have.text",
        "You currently have 2 prepaid dinners remaining.",
      );
    });

    it("the number of prepaid dinners will decrement as they order", () => {
      getDataTestIdElement("dinner-signup-register").click();
      cy.contains("Dinner sign-up registration successful!");
      getDataTestIdElement("dinner-signup-button").click();
      getDataTestIdElement("prepaid-dinners-message").should(
        "have.text",
        "You currently have 1 prepaid dinner remaining.",
      );
    });

    it("the prepaid dinners message will disappear when they have no more prepaid dinners left", () => {
      getDataTestIdElement("dinner-signup-first-name").click().type("1");
      getDataTestIdElement("dinner-signup-register").click();
      cy.contains("Dinner sign-up registration successful!");
      getDataTestIdElement("dinner-signup-button").click();
      getDataTestIdElement("prepaid-dinners-message").should("not.exist");
    });

    it("the user will see the prepaid dinners marked in their orders", () => {
      getDataTestIdElement("dinner-signup-first-name").click().type("2");
      getDataTestIdElement("dinner-signup-register").click();
      cy.contains("Dinner sign-up registration successful!");
      getDataTestIdElement("pay-tab-button").click();
      getDataTestIdElement("total-amount-due").should(
        "have.text",
        "Total amount due: €12.00",
      );
      getDataTestIdElement("ordered_item")
        .should("have.length", 3)
        .each(($orderedItemEl, index) => {
          cy.wrap($orderedItemEl).should(
            "have.text",
            `Dinner sign-up${index ? " (Prepaid)" : ""}`,
          );
        });
      getDataTestIdElement("ordered_item_total")
        .should("have.length", 3)
        .each(($orderedItemTotalEl, index) => {
          cy.wrap($orderedItemTotalEl).should(
            "have.text",
            index ? "€0.00" : "€12.00",
          );
        });
    });

    it("they will not be charged for the prepaid dinners when paying the tab", () => {
      getDataTestIdElement("pay-tab-button").click();
      getDataTestIdElement("radio-input-yes").click();
      getDataTestIdElement("submit-button").click();
      getDataTestIdElement("stripe-subtotal").should(
        "have.text",
        "Subtotal: €12.00",
      );
      getDataTestIdElement("stripe-handling-fee").should(
        "have.text",
        "System Provider Handling Fee: €0.39",
      );
      getDataTestIdElement("stripe-total").should("have.text", "Total: €12.39");
      getDataTestIdElement("stripe_qr_code_image");
      assertStripeLineItemsMatchExpected([
        {
          price_data: {
            currency: "eur",
            product_data: {
              name: "Dinner sign-up (Prepaid)",
            },
            unit_amount: 0,
          },
          quantity: 2,
        },
        {
          price_data: {
            currency: "eur",
            product_data: {
              name: "Dinner sign-up",
            },
            unit_amount: 1200,
          },
          quantity: 1,
        },
        {
          price_data: {
            currency: "eur",
            product_data: {
              name: "System Provider Handling Fee",
            },
            unit_amount: 39,
          },
          quantity: 1,
        },
      ]);
    });

    it("when they pay their tab their prepaid dinner quantity will be decremented", () => {
      triggerSuccessfulStripePayment();
      getDataTestIdElement("checkout-complete-text").should("be.visible");
      cy.request({
        method: "GET",
        url: "http://app:8000/api/test/user",
        qs: { username },
      }).then((response) => {
        cy.wrap(response.body.user.prepaid_dinners_quantity).should("eq", 0);
      });
    });
  },
);
