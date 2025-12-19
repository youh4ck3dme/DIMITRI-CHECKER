// ESM wrapper pre prop-types (CommonJS modul)
// Vite automaticky transformuje CommonJS na ESM
import PropTypes from 'prop-types';

export default PropTypes;
export const {
  array,
  bool,
  func,
  number,
  object,
  string,
  symbol,
  any,
  arrayOf,
  element,
  elementType,
  instanceOf,
  node,
  objectOf,
  oneOf,
  oneOfType,
  shape,
  exact
} = PropTypes;

