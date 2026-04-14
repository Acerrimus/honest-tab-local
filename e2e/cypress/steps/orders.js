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

function generateFormattedTime() {
  const now = new Date();
  const pad = (n) => n.toString().padStart(2, "0");
  const day = pad(now.getDate());
  const month = pad(now.getMonth() + 1);
  const year = now.getFullYear();
  const hours = pad(now.getHours());
  const minutes = pad(now.getMinutes());
  const seconds = pad(now.getSeconds());
  return `${day}/${month}/${year} ${hours}:${minutes}:${seconds}`;
}

export function generateOrderDetails(username, item = "TEST ITEM") {
  return {
    order_id: uuidv4(),
    user_nick_name: username,
    time: generateFormattedTime(),
    item,
    quantity: 1.0,
    price: 1.0,
    total: 1.0,
    receiver: "",
    diet: "",
    allergies: "",
    served: "",
    tax_category: "",
    comment: "",
  };
}

export function createDinnerOrderApi(username, receiver) {
  const dinnerOrder = {
    price: 12.0,
    total: 12.0,
    receiver: receiver,
    diet: "Vegan",
    user_nick_name: username,
    allergies: "",
    synced: false,
    time: generateFormattedTime(),
    served: "",
    item: "Dinner sign-up",
    tax_category: "Food and beverage non-alcoholic",
    order_id: uuidv4(),
    quantity: 1.0,
    comment: "",
  };
  return createUserOrderAPI(dinnerOrder);
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
