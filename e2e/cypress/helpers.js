export function getDataTestIdElement(dataTestid){
  return cy.get(`[data-testid=${dataTestid}]`)
}