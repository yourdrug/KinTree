/**
 * api/index.js
 *
 * Единственная точка входа для всех API-модулей.
 *
 * Использование:
 *   import { familiesApi, personsApi, relationsApi, authApi, loadFamilyTree } from "@/api";
 */

export { http, extractErrorMessage } from "./http";
export { ENDPOINTS } from "./endpoints";
export { authApi } from "./auth";
export { familiesApi } from "./families";
export { personsApi } from "./persons";
export {
  relationsApi,
  buildRelationMaps,
  getPersonRelations,
  toPartialDate,
  formatPartialDate,
  loadFamilyTree,
  createPersonAsChild,
  createPersonAsSpouse,
  createPersonAsSibling,
} from "./relations";
