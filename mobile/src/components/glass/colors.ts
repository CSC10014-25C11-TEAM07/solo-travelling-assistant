// Transmit the scene colour; dark type, rather than a near-white card, supplies contrast.
export const paneOpacity = .56;
const foam = '#F6FCFA';
export const palette = {
  ink: '#0A2929', pine: '#08443F', mist: '#E5F1EF', foam, slate: '#142624', oxide: '#923C31',
  pane: `${foam}${Math.round(255 * paneOpacity).toString(16)}`, rim: '#FFFFFFDE', line: '#85A89F',
  bg: '#E5F1EF', green: '#0A2929', accent: '#08443F', gray: '#142624', white: foam, red: '#923C31', cream: foam,
} as const;
