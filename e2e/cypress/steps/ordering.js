import { getDataTestIdElement } from "../helpers";

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
