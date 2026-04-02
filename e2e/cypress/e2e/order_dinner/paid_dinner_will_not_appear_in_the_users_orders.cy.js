import { getDataTestIdElement } from "../../helpers";
import {
  createUserOrderAPI,
  generateOrderDetails,
  getUserOrdersAPI,
} from "../../steps/orders";
import { createUserAPI, generateUsername, logUserOn } from "../../steps/users";

describe("When a user pays for their dinner", () => {
  it("the dinner does not appear in the user's orders", () => {
    const username = generateUsername();
    createUserAPI(username);
    cy.visit("/");
    logUserOn(username);
    getDataTestIdElement("dinner-signup-button").click();
    getDataTestIdElement("dinner-signup-pay-now").click();
    getDataTestIdElement("stripe_qr_code_image");
    cy.contains("Dinner sign-up registration successful!");
    getUserOrdersAPI(username).then((response) => {
      expect(response.body.orders).to.have.lengthOf(1);
      const order = response.body.orders[0];
      expect(order.item).to.eq("Dinner sign-up");
      expect(order.paid).to.eq("true");
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
