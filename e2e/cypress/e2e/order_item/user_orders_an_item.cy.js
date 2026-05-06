import { getDataTestIdElement } from "../../helpers";
import { getUserOrdersApi } from "../../steps/orders";
import { getPaymentApi } from "../../steps/payments";
import {
  createGuestUserApi,
  generateUsername,
  logUserOn,
} from "../../steps/users";

describe("When a user orders an item", { tags: "@smoke" }, () => {
  const username = generateUsername();
  it("it is successfully ordered", () => {
    createGuestUserApi(username);
    cy.visit("/");
    logUserOn(username);
    getDataTestIdElement("order_item_button")
      .filter(":contains(TEST ITEM (€1.00))")
      .click();
    getDataTestIdElement("item_quantity_input").should("have.value", 1);
    getDataTestIdElement("item_total").contains("Total: €1");
    getDataTestIdElement("item_register").click();
    getDataTestIdElement("view-orders-button").click();
    getDataTestIdElement("ordered_item").contains("TEST ITEM");
    getUserOrdersApi(username).then((userOrdersresponse) => {
      expect(userOrdersresponse.body.orders).to.have.lengthOf(1);
      const order = userOrdersresponse.body.orders[0];
      expect(order.item).to.eq("TEST ITEM");
      getPaymentApi(order.order_id).then((paymentResponse) => {
        expect(paymentResponse.body.payment).to.eq("None found");
      });
    });
  });
});
