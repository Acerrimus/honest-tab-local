import { getDataTestIdElement } from "../../helpers";
import {
  createGuestUserApi,
  generateUsername,
  logUserOn,
} from "../../steps/users";

describe("When a user pays for two items in a row", () => {
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
    getDataTestIdElement("stripe_payment_successful_text").should("be.visible");
    cy.contains("'TEST ITEM' registered succesfully. Thank you!");
    getDataTestIdElement("stripe_dialog_close").click();
    getDataTestIdElement("order_item_button")
      .filter(":contains(TEST ITEM (€1.00))")
      .click();
    getDataTestIdElement("item_pay_now").click();
    getDataTestIdElement("stripe_qr_code_image");
    getDataTestIdElement("stripe_payment_successful_text").should("be.visible");
    cy.contains("'TEST ITEM' registered succesfully. Thank you!");
  });
});
