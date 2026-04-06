import { getDataTestIdElement } from "../../helpers";
import {
  createUserOrderAPI,
  generateOrderDetails,
  getUserOrdersAPI,
} from "../../steps/orders";
import { createUserAPI, generateUsername, logUserOn } from "../../steps/users";

describe("When a user pays for an item", () => {
  it("the item will be registered but not appear in the user's orders", () => {
    const username = generateUsername();
    createUserAPI(username);
    cy.visit("/");
    logUserOn(username);
    getDataTestIdElement("order_item_button")
      .filter(":contains(TEST ITEM (€1.00))")
      .click();
    getDataTestIdElement("item_pay_now").click();
    getDataTestIdElement("stripe_payment_successful_text").should("be.visible");
    cy.contains("'TEST ITEM' registered succesfully. Thank you!")
    getUserOrdersAPI(username).then((response) => {
      expect(response.body.orders).to.have.lengthOf(1);
      const order = response.body.orders[0];
      expect(order.item).to.eq("TEST ITEM");
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
