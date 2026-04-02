import { getDataTestIdElement } from "../helpers";
import { v4 as uuidv4 } from "uuid";

export function orderDinner(username) {
  getDataTestIdElement("dinner-signup-button").click();
  getDataTestIdElement("dinner-signup-first-name").should(
    "have.value",
    username,
  );
  getDataTestIdElement("dinner-signup-last-name").should("have.value", "Test");
  getDataTestIdElement("dinner-signup-allergies").should("have.value", "Nuts");
  getDataTestIdElement("dinner-signup-register").click();
}

export function clickTestItemButton() {
  getDataTestIdElement("order_item_button")
    .filter(":contains(TEST ITEM (€1.00))")
    .click();
}

export function generateOrderDetails(username) {
  return {
    order_id: uuidv4(),
    user_nick_name: username,
    time: "01/01/2025 12:00:00",
    item: "TEST ITEM",
    quantity: 1.0,
    price: 1.0,
    total: 1.0,
    receiver: "",
    diet: "",
    allergies: "",
    served: "",
    tax_category: "",
    comment: "",
    paid: false,
    paid_time: "",
    method: "",
    checkout_staff: "",
  };
}

export function createUserOrderAPI(qs) {
  return cy.request({
    method: "POST",
    url: "http://app:8000/api/test/orders",
    qs,
  });
}

export function getUserOrdersAPI(username) {
  return cy.request({
    url: "http://app:8000/api/test/orders",
    qs: { username },
  });
}
