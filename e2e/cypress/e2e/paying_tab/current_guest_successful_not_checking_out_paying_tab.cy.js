import { getDataTestIdElement } from "../../helpers";
import {
  createUserOrderAPI,
  generateOrderDetails,
  getUserOrdersAPI,
} from "../../steps/orders";
import {
  createGuestUserApi,
  generateUsername,
  logUserOn,
} from "../../steps/users";

describe("When a current guest successfully pays their tab and chooses to not check out", () => {
  const username = generateUsername();
  it("they will stay logged in and their paid items will not be in their tab", () => {
    createGuestUserApi(username);
    const itemNames = [1, 2, 3].map((num) => `REGISTERED TEST ITEM${num}`);
    const orderDetails = itemNames.map((itemName) =>
      generateOrderDetails(username, itemName),
    );
    cy.wrap(orderDetails).each((orderDetail) => {
      createUserOrderAPI(orderDetail);
    });
    cy.visit("/");
    logUserOn(username);
    getDataTestIdElement("pay-tab-button").click();
    getDataTestIdElement("ordered_item").should("have.lengthOf", 3);
    getDataTestIdElement("total-amount-due").should(
      "have.text",
      "Total amount due: €3.00",
    );
    getDataTestIdElement("pay-tab-button").click();
    getDataTestIdElement("radio-input-no").click();
    getDataTestIdElement("submit-button").click();
    getDataTestIdElement("stripe_payment_successful_text").should("be.visible");
    getDataTestIdElement("stripe_dialog_close").click();
    cy.contains("Tab paid successfully!");
    getDataTestIdElement("pay-tab-button").click();
    getDataTestIdElement("total-amount-due").should(
      "have.text",
      "Total amount due: €0.00",
    );
    getDataTestIdElement("ordered_item").should("not.exist");
  });

  it("all their orders will have a paid status", () => {
    cy.waitUntil(() =>
      getUserOrdersAPI(username).then((response) =>
        response.body.orders.every((order) => order.paid),
      ),
    );
  });
});
