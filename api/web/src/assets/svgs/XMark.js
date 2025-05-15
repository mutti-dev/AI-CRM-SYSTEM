import * as React from "react";
const XMark = (props) => (
  <svg
    width="800px"
    height="800px"
    viewBox="0 0 16 16"
    xmlns="http://www.w3.org/2000/svg"
    xmlnsXlink="http://www.w3.org/1999/xlink"
    {...props}
  >
    <rect width={16} height={16} id="icon-bound" fill="none" />
    <polygon points="14.707,2.707 13.293,1.293 8,6.586 2.707,1.293 1.293,2.707 6.586,8 1.293,13.293 2.707,14.707 8,9.414  13.293,14.707 14.707,13.293 9.414,8 " />
  </svg>
);
export default XMark;
