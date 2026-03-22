export function createUser(username){
    cy.get('[data-testid="sign-up-user-button"]').click();
    cy.get('[data-testid="user-name-input"]').click().type(username);
    cy.get('[data-testid="first-name-input"]').click().type("Cypress");
    cy.get('[data-testid="last-name-input"]').click().type("Test");
    cy.get('[data-testid="phone-number-input"]').click().type("0123456789");
    cy.get('[data-testid="email-input"]').click().type("test@test.com");
    cy.get('select[name="diet"]').select("Vegan", { force: true });
    cy.get('[data-testid="allergies-input"]').click().type("Nuts");
    cy.get('[data-testid="radio-input-yes"]').click();
    cy.get('[data-testid="user-submit-button"]').click();
}

export function logUserOn(username, password="test@"){
    cy.get(`[data-testid="user-button-${username}"]`, { timeout: 10000 }).click();
    cy.get(`[data-testid="user-email-password"]`).click().type(password);
    cy.get(`[data-testid="password-submit-button"]`).click();

}