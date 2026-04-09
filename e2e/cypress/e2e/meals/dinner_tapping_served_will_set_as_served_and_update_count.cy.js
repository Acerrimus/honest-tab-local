import { getDataTestIdElement } from "../../helpers";
import { createDinnerOrderApi } from "../../steps/orders";
import { createUserAPI, generateUsername } from "../../steps/users";

function getTotalServedInt(text) {
  return parseInt(text.split(" ").at(-1));
}

describe("When an admin user clicks served for a guest's dinner meal", () => {
  const username = generateUsername();
  const receiver = `${username.toUpperCase()} TEST`;

  it("it will show as served and increment the served count", function () {
    createUserAPI(username);
    createDinnerOrderApi(username, receiver);
    cy.visit("/admin/dinner");
    cy.contains(receiver);
    getDataTestIdElement("total-served").invoke("text").as("totalServed");
    getDataTestIdElement("total-guests-served")
      .invoke("text")
      .as("totalGuestsServed");
    getDataTestIdElement("meal-row")
      .filter(`:contains(${receiver})`)
      .find(`[data-testid=served-button]`)
      .then(($servedButtonEl) => {
        expect($servedButtonEl).to.have.text("✖️");
        cy.wrap($servedButtonEl).click().should("have.text", "✅");
        getDataTestIdElement("total-served").should(
          "have.text",
          `Total served: ${getTotalServedInt(this.totalServed) + 1}`,
        );
        getDataTestIdElement("total-guests-served").should(
          "have.text",
          `Total served: ${getTotalServedInt(this.totalGuestsServed) + 1}`,
        );
      });
  });

  it("and when clicked again it will show as not served and decrement the served count", function () {
    cy.visit("/admin/dinner");
    cy.waitUntil(
      () => {
        let count = 0;
        let receiverHasBeenServed = false;
        Cypress.$("[data-testid=meal-row]").each((_, mealRow) => {
          if (
            Cypress.$(mealRow).find("[data-testid=served-button]").text() !==
            "✅"
          ) {
            return;
          }
          if (
            Cypress.$(mealRow).find("[data-testid=meal-receiver]").text() ===
            receiver
          ) {
            receiverHasBeenServed = true;
          }
          count++;
        });
        return (
          receiverHasBeenServed &&
          getTotalServedInt(Cypress.$("[data-testid=total-served]").text()) ===
            count
        );
      },
      { timeout: 20000 },
    );
    getDataTestIdElement("total-served").invoke("text").as("totalServed");
    getDataTestIdElement("total-guests-served")
      .invoke("text")
      .as("totalGuestsServed");
    getDataTestIdElement("meal-row")
      .filter(`:contains(${receiver})`)
      .find(`[data-testid=served-button]`)
      .then(($servedButtonEl) => {
        expect($servedButtonEl).to.have.text("✅");
        cy.wrap($servedButtonEl).click().should("have.text", "✖️");
        getDataTestIdElement("total-served").should(
          "have.text",
          `Total served: ${getTotalServedInt(this.totalServed) - 1}`,
        );
        getDataTestIdElement("total-guests-served").should(
          "have.text",
          `Total served: ${getTotalServedInt(this.totalGuestsServed) - 1}`,
        );
      });
  });
});
