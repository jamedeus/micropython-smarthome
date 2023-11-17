import React from 'react';
import InputWrapper from './InputWrapper';

function SensorPinSelect({ key, id, param, value, onChange }) {
    return (
        <InputWrapper label="Pin">
            <select className="form-select pin-select" value={value} autoComplete="off" /*onchange="pinSelected(this)"*/ onChange={(e) => onChange(param, e.target.value)} required>
                <option>Select pin</option>
                <option value="4">4</option>
                <option value="5">5</option>
                <option value="13">13</option>
                <option value="14">14</option>
                <option value="15">15</option>
                <option value="16">16</option>
                <option value="17">17</option>
                <option value="18">18</option>
                <option value="19">19</option>
                <option value="21">21</option>
                <option value="22">22</option>
                <option value="23">23</option>
                <option value="25">25</option>
                <option value="26">26</option>
                <option value="27">27</option>
                <option value="32">32</option>
                <option value="33">33</option>
                <option value="34">34</option>
                <option value="35">35</option>
                <option value="36">36</option>
                <option value="39">39</option>
            </select>
        </InputWrapper>
    );
}

export default SensorPinSelect;
