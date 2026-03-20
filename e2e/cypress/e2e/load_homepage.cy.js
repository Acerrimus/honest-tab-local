describe("When loading the homepage", () => {
  it("loads successfully", () => {
    cy.visit("/")
    cy.get('[data-testid="title"]').contains("Olive Branch");
  });
});