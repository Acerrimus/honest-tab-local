import { getDataTestIdElement } from "../../helpers";
import {
  createUserOrderAPI,
  generateOrderDetails,
  getUserOrdersAPI,
} from "../../steps/orders";
import { createUserAPI, generateUsername, logUserOn } from "../../steps/users";

describe("When a user pays for their breakfast", () => {
  it("the breakfast does not appear in the user's orders", () => {
    const username = generateUsername();
    createUserAPI(username);
    cy.visit("/");
    logUserOn(username);
    getDataTestIdElement("breakfast-signup-button").click();
    getDataTestIdElement("breakfast-signup-item-select").click();
    getDataTestIdElement("breakfast-signup-item-option").first().click();
    getDataTestIdElement("breakfast-pay-now").click();
    getDataTestIdElement("stripe_qr_code_image");
    cy.contains("Breakfast sign-up registration successful!");
    getUserOrdersAPI(username).then((response) => {
      expect(response.body.orders).to.have.lengthOf(1);
      const order = response.body.orders[0];
      expect(order.item).to.eq("Breakfast sign-up");
      expect(order.paid).to.be.true
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
