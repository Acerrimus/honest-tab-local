import { getDataTestIdElement } from "../../helpers";
import { getUserOrdersApi } from "../../steps/orders";
import { getPaymentApi } from "../../steps/payments";
import {
  createGuestUserApi,
  generateUsername,
  logUserOn,
} from "../../steps/users";

describe("When a user orders a custom item", () => {
  const username = generateUsername();
  const customItemName = "New custom item";
  it("it is successfully ordered", () => {
    createGuestUserApi(username);
    cy.visit("/");
    logUserOn(username);
    getDataTestIdElement("custom-item-button").click();
    getDataTestIdElement("custom-item-name-input").click().type(customItemName);
    getDataTestIdElement("custom-item-price-input").click().type("1");
    getDataTestIdElement("custom-item-register-button").click();
    cy.contains(`'${customItemName}' registered succesfully. Thank you!`);
    getDataTestIdElement("user-page-heading").contains(`Hello ${username}`);
    getUserOrdersApi(username).then((userOrdersresponse) => {
      expect(userOrdersresponse.body.orders).to.have.lengthOf(1);
      const order = userOrdersresponse.body.orders[0];
      expect(order.item).to.eq(customItemName);
      expect(order.quantity).to.eq(1.0);
      expect(order.price).to.eq(1.0);
      expect(order.total).to.eq(1.0);
    });
  });
});
