import pytest

# Sample Solidity code used across multiple test files
SAMPLE_ERC20 = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract MyToken is ERC20, Ownable {
    uint256 public maxSupply;
    mapping(address => bool) public blacklist;

    constructor(uint256 _maxSupply) ERC20("MyToken", "MTK") Ownable(msg.sender) {
        maxSupply = _maxSupply;
    }

    function mint(address to, uint256 amount) external onlyOwner {
        require(totalSupply() + amount <= maxSupply, "Exceeds max supply");
        _mint(to, amount);
    }

    function burn(uint256 amount) external {
        _burn(msg.sender, amount);
    }

    function addToBlacklist(address account) external onlyOwner {
        blacklist[account] = true;
    }

    function balanceOf(address account) public view override returns (uint256) {
        return super.balanceOf(account);
    }
}
"""

SAMPLE_VULNERABLE = """// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract Vulnerable {
    mapping(address => uint256) public balances;

    function deposit() external payable {
        balances[msg.sender] += msg.value;
    }

    function withdraw(uint256 amount) external {
        require(balances[msg.sender] >= amount);
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success);
        balances[msg.sender] -= amount;
    }

    function destroy() external {
        selfdestruct(payable(msg.sender));
    }

    function checkOwner() external view returns (address) {
        return tx.origin;
    }
}
"""

SAMPLE_MINIMAL = """// SPDX-License-Identifier: MIT
pragma solidity 0.8.20;

contract SimpleStorage {
    uint256 private _value;
    event ValueChanged(uint256 newValue);

    function set(uint256 value) external {
        _value = value;
        emit ValueChanged(value);
    }

    function get() external view returns (uint256) {
        return _value;
    }
}
"""
