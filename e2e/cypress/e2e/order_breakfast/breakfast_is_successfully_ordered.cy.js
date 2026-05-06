import { getDataTestIdElement } from "../../helpers";
import { assertBreakfastLineItemsMatchExpected } from "../../steps/stripe";
import {
  createGuestUserApi,
  generateUsername,
  logUserOn,
} from "../../steps/users";

describe("When a user orders breakfast", { testIsolation: false, tags: "@smoke" }, () => {
  const username = generateUsername();
  it("it is successfully ordered", () => {
    createGuestUserApi(username);
    cy.visit("/");
    logUserOn(username);
    getDataTestIdElement("breakfast-signup-button").click();
    getDataTestIdElement("breakfast-signup-first-name").should(
      "have.value",
      username,
    );
    getDataTestIdElement("breakfast-signup-last-name").should(
      "have.value",
      "Test",
    );
    getDataTestIdElement("breakfast-signup-item-select").click();
    getDataTestIdElement("breakfast-signup-item-option").first().click();
    getDataTestIdElement("breakfast-signup-allergies").should(
      "have.value",
      "Nuts",
    );
    getDataTestIdElement("breakfast-signup-register").click();
    getDataTestIdElement("view-orders-button").click();
    getDataTestIdElement("ordered_item").contains("Breakfast sign-up (Vegan)");
  });

  it("will appear correctly in the line items when paying the tab", () => {
    getDataTestIdElement("pay-tab-button").click();
    getDataTestIdElement("radio-input-yes").click();
    getDataTestIdElement("submit-button").click();
    getDataTestIdElement("stripe_qr_code_image");
    assertBreakfastLineItemsMatchExpected();
  });

  it("the order appears in the breakfast list", () => {
    cy.visit("/admin/breakfast");
    getDataTestIdElement("meal-receiver")
      .filter(`:contains(${username.toUpperCase()} TEST)`)
      .should("have.length", 1);
  });
});
