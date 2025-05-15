import * as React from "react";
const Schedule = (props) => (
  <svg
    fill="#000000"
    width="800px"
    height="800px"
    viewBox="0 0 24 24"
    id="schedule"
    data-name="Line Color"
    xmlns="http://www.w3.org/2000/svg"
    className="icon line-color"
    {...props}
  >
    <path
      id="primary"
      d="M14,16l1,5,6-6ZM20,4H4A1,1,0,0,0,3,5V20a1,1,0,0,0,1,1H15l6-6V5A1,1,0,0,0,20,4Z"
      style={{
        fill: "none",
        stroke: "rgb(0, 0, 0)",
        strokeLinecap: "round",
        strokeLinejoin: "round",
        strokeWidth: 2,
      }}
    />
    <path
      id="secondary"
      d="M20,4H4A1,1,0,0,0,3,5V9H21V5A1,1,0,0,0,20,4ZM17,3V5M12,3V5M7,3V5"
      style={{
        fill: "none",
        stroke: "rgb(44, 169, 188)",
        strokeLinecap: "round",
        strokeLinejoin: "round",
        strokeWidth: 2,
      }}
    />
  </svg>
);
export default Schedule;
