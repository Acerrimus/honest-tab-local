export function getTotalServedInt(text) {
  return parseInt(text.split(" ").at(-1));
}

export function waitForReceiverServedStatusAndTotalCountToRender(receiver) {
  cy.waitUntil(
    () => {
      let count = 0;
      let receiverHasBeenServed = false;
      Cypress.$("[data-testid=meal-row]").each((_, mealRow) => {
        if (
          Cypress.$(mealRow).find("[data-testid=served-button]").text() !== "✅"
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
}
