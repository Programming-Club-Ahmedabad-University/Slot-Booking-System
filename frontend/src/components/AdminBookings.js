import React from 'react';
import axios from 'axios';
import moment from 'moment';
import { Card, Button, Row, Col, Empty, Modal, Input, Table } from 'antd';
import UserContext from '../context/usercontext';

class AdminBooking extends React.Component {
	static contextType = UserContext;

	constructor(props) {
		super(props);
		this.state = {
			response: [],
			modalVisible: false,
			feedback: null,
			accept: null,
			id: null,
			mainSlot: null,
		};
		this.fetchData = this.fetchData.bind(this);
	}

	columns = [
		{
			title: 'Booking Date',
			dataIndex: 'booking_date',
			width: 150,
			fixed: 'left',
			sorter: (a, b) => moment(a['booking_date']) - moment(b['booking_date']),
			sortDirections: ['descend', 'ascend'],
		},
		{
			title: 'Requested By',
			dataIndex: 'user',
			sorter: (a, b) => a['user'].length - b['user'].length,
			sortDirections: ['descend', 'ascend'],
		},
		{
			title: 'Room #',
			dataIndex: 'room_number',
			sorter: (a, b) => a['room_number'] - b['room_number'],
			sortDirections: ['descend', 'ascend'],
		},
		{
			title: 'Room Name',
			dataIndex: 'room_name',
			sorter: (a, b) => a['room_name'].length - b['room_name'].length,
			sortDirections: ['descend', 'ascend'],
		},
		{
			title: 'Purpose of Booking',
			dataIndex: 'purpose_of_booking',
			sorter: (a, b) => a['purpose_of_booking'].length - b['purpose_of_booking'].length,
			sortDirections: ['descend', 'ascend'],
		},
	];

	clashSlots = () => {
		var clash = [];
		const { mainSlot, response } = this.state;
		if (this.state.accept !== false && mainSlot !== null && response !== null) {
			response.map((values, index) => {
				if (
					values['room_id'] === mainSlot['room_id'] &&
					values['start_timing'] === mainSlot['start_timing'] &&
					values['booking_date'] === mainSlot['booking_date'] &&
					values['id'] !== mainSlot['id']
				) {
					clash.push(values);
				}
			});
		}
		return clash.length >= 1 ? (
			<>
				<p>The following requests will be automatically declined as they clash with current request</p>
				<Table
					pagination={false}
					style={{ marginBottom: 20 }}
					dataSource={clash}
					columns={clash && this.columns}
					scroll={{ x: 600, y: 300 }}
				/>
			</>
		) : null;
	};

	componentDidMount() {
		this.fetchData();
	}

	fetchData() {
		const config = {
			headers: { Authorization: `Token ${this.context.token}` },
		};
		axios.get('http://127.0.0.1:8000/api/filter/adminfilter/pending', config).then((res) => {
			this.setState({ response: res.data }, () => {
				console.log(this.state.response);
			});
		});
	}

	handleButtonClick(event) {
		event.preventDefault();
		let message = this.state.feedback;
		if (message === '' || message === null || message === false) {
			message = 'Admin has not given any feedback';
		}
		const config = {
			headers: { Authorization: `Token ${this.context.token}` },
		};
		axios
			.post(
				`http://127.0.0.1:8000/api/filter/adminfilter/pending`,
				{
					id: this.state.id,
					admin_did_accept: this.state.accept,
					admin_feedback: message,
				},
				config
			)
			.then((_res) => {
				this.fetchData();
				this.setState({ modalVisible: false });
			});
	}

	render() {
		if (this.state.response.length === 0) {
			return <Empty description={<span>All Bookings have been attended</span>} />;
		}
		return (
			<Row gutter={[16, { xs: 32, sm: 24, md: 16, lg: 8 }]} style={{ justifyContent: 'space-around' }}>
				{this.state.response !== null &&
					this.state.response.map((value, index) => (
						<Col className="gutter-row" span={{ xs: 24, sm: 12, md: 8, lg: 6 }} key={index}>
							<Card size="large" title={'Request ' + (index + 1)} style={{ width: 300 }} hoverable>
								<p>Requested By: {value['user']}</p>
								<p>Room: {value['room_number'] + ' - ' + value['room_name']}</p>
								<p>Date: {value['booking_date']}</p>
								<p>From: {moment(value['start_timing'], 'HH:mm:ss').format('HH:mm')}</p>
								<p>To: {moment(value['end_timing'], 'HH:mm:ss').format('HH:mm')}</p>
								<p>Reason: {value['purpose_of_booking']}</p>
								<p>
									<>
										<Button
											type="primary"
											size="large"
											style={{ marginRight: 10 }}
											onClick={(e) => {
												e.preventDefault();
												this.setState({
													id: value['id'],
													mainSlot: value,
													modalVisible: true,
													accept: true,
												});
											}}
										>
											Accept
										</Button>
										<Button
											type="primary"
											size="large"
											danger
											onClick={(e) => {
												e.preventDefault();
												this.setState({
													id: value['id'],
													mainSlot: value,
													modalVisible: true,
													accept: false,
												});
											}}
										>
											Decline
										</Button>
									</>
								</p>
							</Card>
						</Col>
					))}
				<Modal
					title="Please enter the feedback for selected response"
					centered
					visible={this.state.modalVisible}
					onOk={(e) => {
						this.handleButtonClick(e);
					}}
					onCancel={() => {
						this.setState({ modalVisible: false });
					}}
				>
					{this.clashSlots()}
					<Input.TextArea
						placeholder="Enter your reason for taking this action"
						autoSize={{ minRows: 4, maxRows: 8 }}
						onChange={(v) => {
							this.setState({ feedback: v.target.value });
						}}
					/>
				</Modal>
			</Row>
		);
	}
}

export default AdminBooking;
