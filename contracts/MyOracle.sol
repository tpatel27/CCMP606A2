// CCMP 606 Assignment 2
// Oracle Smart Contract
// Author: Tejas Patel
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

  /**
   * @title MyOracle
   * @dev tejaspatel 
   */

contract MyOracle {

    address public owner;
    uint public etherPriceInUSD;

    // Event emitted when the price is updated
    event PriceUpdated(uint newPrice);

    // Event emitted when an update is requested
    event UpdateRequested();

    // Constructor to set the owner as the contract deployer
    constructor() {
        owner = msg.sender;
    }

    // Function allowing the owner to set the Ether price in USD
    function setEtherPrice(uint _price) external {
        require(msg.sender == owner, "Only the contract owner can set the price");
        etherPriceInUSD = _price;
        emit PriceUpdated(_price);
    }

    // Function to retrieve the current Ether price in USD
    function getEtherPrice() external view returns (uint) {
        return etherPriceInUSD;
    }

    // Function to request an update (emits the UpdateRequested event)
    function requestUpdate() external {
        emit UpdateRequested();
    }
}