import { getDataTestIdElement } from "../../helpers";
import { getTotalServedInt } from "../../steps/meals";
import { generateReceiver } from "../../steps/orders";
import { createVolunteerUserApi, generateUsername } from "../../steps/users";

describe(
  "When an admin user clicks served for a volunteer's dinner meal",
  { testIsolation: false, tags: "@smoke" },
  () => {
    const username = generateUsername();
    const receiver = generateReceiver(username);

    it("it will show as served and increment the volunteers served count with the guests served staying the same", function () {
      createVolunteerUserApi(username);
      cy.visit("/admin/dinner");
      cy.contains(receiver, { timeout: 60000 });
      getDataTestIdElement("total-served").invoke("text").as("totalServed");
      getDataTestIdElement("total-guests-served")
        .invoke("text")
        .as("totalGuestsServed");
      getDataTestIdElement("total-volunteers-served")
        .invoke("text")
        .as("totalVolunteersServed");
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
            this.totalGuestsServed,
          );
          getDataTestIdElement("total-volunteers-served").should(
            "have.text",
            `Total served: ${getTotalServedInt(this.totalVolunteersServed) + 1}`,
          );
        });
    });

    it("and when clicked again it will show as not served and decrement the volunteers served count with the guests served count staying the same", function () {
      getDataTestIdElement("total-served").invoke("text").as("totalServed");
      getDataTestIdElement("total-volunteers-served")
        .invoke("text")
        .as("totalVolunteersServed");
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
            this.totalGuestsServed,
          );
          getDataTestIdElement("total-volunteers-served").should(
            "have.text",
            `Total served: ${getTotalServedInt(this.totalVolunteersServed) - 1}`,
          );
        });
    });
  },
);
